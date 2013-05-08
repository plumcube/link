import json

class Cacheable(object):
    """An object that has a cache built into it for storing data.
    """
    def __init__(self, read_permissions = None, write_permissions = None):
        """
        Read permissions is whether the user has read or write access to this db
        Not sure if this will ever be helpful
        """
        super(Cacheable, self).__init__()
        self.cache = {}

    def cache_put(self, key, data, read_type = None):
        """
        Put <key> into the cache into the cache.  If Link is configured to it
        will put it into the end datastore.  Will also make sure that it has
        clean data before writing::

            key: the key that you want to store data at
            data: the data that you want to cache
        """
        self.cache[key] = data

    def cache_get(self, key, read_type = None):
        """
        will get the key from the cache.  You can make it so that it will go to
        the underlying database. Takes care of dirty data for
        you...somehow...figure out how to do that 

            key: the key of the data you want to look up in cache
        """
        return self.cache.get(key)

class Single(object):
    """Creates a singleton.

    """
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Single, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

import datetime

class APIEncoder(json.JSONEncoder):
    """The JSON encoder we use for our APIs.

    """
    def default(self, obj):
        # FIXME: Need to do type comparison, not isinstance().
        if isinstance(obj, APIObject):
            if isinstance(obj, APIResponse):
                return obj.response
            return obj.message

        #we will use the default format...but we probably want to make this
        #configurable
        if isinstance(obj, datetime.datetime):
            return str(obj)

        return super(APIEncoder, self).encode(obj)

    def encode(self, obj):
        return super(APIEncoder, self).encode(obj)


class APIObject(object):
    """An APIObject could also be a node.

    The key is really a key_tail.  It does not need to have a hierarchy.

    """

    def __init__(self,
                 message  = None,
                 warnings = None,
                 error    = None
                 ):
        self._message = message
        self.error = error
        self.warnings = warnings

    @classmethod
    def api_object_name(cls):
        return cls.__name__.lower()

    def __getitem__(self, name):
        try:
            return self.json[name]
        except:
            raise Exception('no json stored in this APIObject or API Response')

    def __iter__(self):
        return self.json.__iter__()

    def get(self, name):
        return self.message.get(name)

    def __str__(self):
        return json.dumps(self.message , cls = APIEncoder)

    def __getitem__(self, key):
        return self.message[key]

    @property
    def response_label(self):
        """Only gets called the first time, then it is cached
        in self.NAME.

        """
        return self.api_object_name()

    @property
    def response(self):
        _json = {}

        # If there is an error don't continue.
        if self.error:
            _json['error'] = self.error
            return _json

        _json['status'] = 'ok'

        if self.message!=None:
            _json['response'] = { self.response_label: self.message }

        if self.warnings:
            _json['warnings'] =  self.warnings

        return _json

    @property
    def message(self):
        return self._message

    def set_message(self, message):
        self._message = message


from utils import array_paginate
import types

class APIResponse(APIObject):
    """Used to help make standardized JSON responses to API
    calls.

    """
    def __init__(self,
                 message     = None,
                 warnings    = None,
                 error       = None,
                 seek        = None,
                 response_id = None,
                 auth        = None
                 ):
        super(APIResponse, self).__init__(message, error=error, warnings=warnings)
        if seek:
            self.seek(*seek)
        self._pages = None
        if callable(auth):
            self.auth = auth()
        self.response_id = response_id

    def auth(self):
        raise NotImplementedError()

    def seek(self, *kargs):
        raise NotImplementedError()

    def __str__(self):
        return json.dumps(self.response, cls=APIEncoder)

    def paginate(self, per_page=100):
        """Returns you an iterator of this response chunked
        into per_page items per page.

        """
        self._pages = array_paginate(per_page, self.message, pad=False)

    def next_page(self):
        """Returns the next page that is in the generator.

        """
        if not self._pages:
            self.paginate()
        try:
            page = self._pages.next()
        except StopIteration as e:
            # If we are done then set the message to nothing
            # FIXME: This seems wrong.
            self.set_message([])
            return self

        message = [x for x in page if x is not None]
        self.set_message(message)
        #TODO: need a test for this
        return self

    @property
    def response(self):
        _json = {}

        #if there is an error don't continue
        if self.error:
            _json['error'] = self.error
            return _json
        
        _json['status'] = 'ok'

        if self.message!=None:
            _json['response'] = { self.response_label: self.message }

        if self.warnings:
            _json['warnings'] =  self.warnings

        if self.response_id:
            _json['response_id'] = self.response_id

        return _json


