import pickle
import inspect
from hobonaut.models.redis_connection import rc, rn
from hobonaut.models import redis_connection
import time


def write(key, data, timeout=86400):
    """set(), which would be a better name, is also an internal function, so
    use 'write' as an alternative
    
    @param key: Ientifies the data in redis
    @param data: The data that will be pickled and commited to redis
    @param timeout=86400: Timeout in seconds. 86400s=1d is default
    """
    rc(redis_connection.REDIS_CACHE_DB).set(rn(key), pickle.dumps(data))
    rc(redis_connection.REDIS_CACHE_DB).expire(rn(key), timeout)


def mread(*keys):
    pipeline = rc(redis_connection.REDIS_CACHE_DB).pipeline()
    for key in keys:
        pipeline.get(rn(key))
    values = pipeline.execute()
    
    unpickled = []
    for value in values:
        if value is None:
            unpickled.append(value)
        else:
            unpickled.append(pickle.loads(value))
            
    return unpickled


def read(key, data_provider, data_provider_parameters = []):
    """The complement to write would be read, not get - and set() can't be
    used.
    
    Articles is stored as a string in redis with SET, since SET is
    O(1) and all other types are O(n)+ on retrieval. To be stored as a
    string, it has to be pickled (serialized) and unpickled.
    """
    data = rc(redis_connection.REDIS_CACHE_DB).get(rn(key))
    if data is None:
        data = data_provider(*data_provider_parameters)
        write(key, data)
    else:
        data = pickle.loads(data)
        
    return data


def delete(key):
    rc(redis_connection.REDIS_CACHE_DB).delete(rn(key))
   
    
class ObjectNotFromPipelineError(Exception):
    pass
    
    
class ObjectNotFoundError(Exception):
    def __init__(self, key):
        self.key = key
    
    def __str__(self):
        return 'Object identified by "{0}" provided no data'.format(self.key)
      
        
class FieldNotFoundError(Exception):
    def __init__(self, field):
        self.field = field
        
    def __str__(self):
        return 'Field "{0}" was accessed, but did not exist'.format(self.field)
        
        
class MissingMultiloadAttributeError(Exception):
    def __init__(self, attribute):
        self._attribute = attribute
        
    def __str__(self):
        return '''The instance is missing an attribute that is required for
Multiload to work. These attributes are required:
- self._key - String containing the cache key
- self._get_data_all - Method that provides data that will be cached

The instance is missing the following attribute: {0}
'''.format(self._attribute)




class Multiload(object):
    """Multiload() provides a base class that handles bulk cache reading and
    writing for derived classes. Many cache storages such as Memcached or Redis
    provide a way to retrieved multiple keys in one request for higher performance,
    which this class uses. On writes the cached data is updated, not invalidated.
    Even often updated data will benefit from Multiloads cache strategy.
    
    #The process:
    
    Instances of derived classes are registered when Multiload.__init__() is
    called. References to their instance are stored in the static @_pipeline list.
    When any of the registered instances tries to access data, the data for all
    instances in @_pipeline is loaded in bulk and cached in the static _data dict.
    The @_pipeline is emptied, and further data access from a different instance
    finds its data in @_data.
    
    #Callback system
    
    Some functions (e.g. rem()) can execute a callback if the child clas
    implemented it. Callbacks are non-public methods that start with '_cb'.
    Available callbacks:
    
    self._cb_rem(deleted_fields) - Takes a list of fields that were deleted from
        the cache by rem(). Should delete the fields from the main data storage.
    
    #Required attributes
    
    For the process to work, the derived classes have to implement certain methods
    and set certain attributes:
    
    self._key - Attribute/String, has to be unique across all instances that might
        be registered. A combination of class name and id is sufficent. Has to be
        set before the pipeline is loaded is called. This is usually done in
        the derived classes constructor.
    
    self._get_data_all - A method that provides all data that the instance might
        require. It's called when a cache miss for @self._key occurrs to store data
        in the cache and may be fairly costly (complex queries, multiple data
        storages)
    
    self.set - Or some other accessor. 'set' is recommended as a name to have an
        opposite to get(), but it could be anything. It just has to call
        _set_data with a dict containing the name-value pairs to set. _set_data
        updates the cache, so the cached data will not be stale
    """
    def __init__(self):
        """This class has to be derived and can't be instanciated directly
        
        @todo Switch get, set, has to callback architecture like rem()
        """
        Multiload._register(self)
    
    _pipeline = []
    """pipeline is a list of instances for which data will be loaded in
    parallel. self._get_data_all() is called and the return value stored in
    redis.
    """
    
    _pipeline_loaded = False
    """Used to signal _get_data() to retrieve data only once. Is reset when
    new objects are _registered
    """
    
    _data = {}

    @classmethod    
    def _register(cls, instance):
        """Starts a new pipeline. Reset self._pipeline_loaded accordingly
        """
        cls._pipeline_loaded = False
        cls._pipeline.append(instance)
        
    @classmethod
    def _store(cls, instance, data):
        """Stores data as a string in redis under key
        """
        write(instance._get_key(), data)
        
    @classmethod
    def _pipeline_load(cls):
        """Loads data for all pipelined keys
        """
        keys = []
        
        for instance in cls._pipeline:
            keys.append(instance._get_key())
        from_cache = mread(*keys)
        i = 0
        for instance in cls._pipeline:
            """from_cache contains objects returned from cache in a list. The
            value is either:
                - None: The object was not in cache
                - String: The data stored in cache
            
            from_cache is exactly as long as and can be mapped to
            self._pipeline, which contains instances.
            
            If cache did not contain key, execute provider and store data in
            cache. Provider will throw ObjectNotFoundError() if the object
            does not exist in persistent storage. Set data to None to mark this
            in self._data.
            
            If cache returned something, unpickle it and put data in self._data
            """ 
            if from_cache[i] is None:
                try:
                    data = instance._get_data_all()
                    cls._store(instance, data)
                except AttributeError:
                    raise MissingMultiloadAttributeError('self._get_data_all')
                except ObjectNotFoundError:
                    data = None
            else:
                data = from_cache[i]
            i = i + 1
            cls._data[instance._get_key()] = data
        """Reset pipeline (so data isn't loaded twice) and mark pipeline
        as loaded
        """
        cls._pipeline = []
        cls._pipeline_loaded = True
        
    @classmethod
    def _get_data(cls, instance, *fields):
        key = instance._get_key()
        if key not in cls._data and not cls._pipeline_loaded:
            """Only execute pipeline if key does not exist (was not yet loaded)
            
            This prevents pipeline from being executed if new objects are
            registered and old accessed.
            """
            cls._pipeline_load()
        if not key in cls._data:
            """Requesting data for an object (key) that was not _register'd
            """
            raise ObjectNotFromPipelineError(key)
        if cls._data[key] is None:
            """Object does not exist in redis.
            """
            raise ObjectNotFoundError(key)
        values = []
        for field in fields:
            if not field in cls._data[key]:
                """Trying to access a field that did not exist. Probably
                because the objects data structure changed and the cache is
                stale.
                """
                raise FieldNotFoundError(field)
            values.append(cls._data[key][field])
        """If only one field was requested, return the value directly. If
        multiple values were requested, return a list
        """        
        if len(values) == 1:
            return values[0]
        else:
            return values
    
    @classmethod
    def cleanup(cls, request):
        cls._pipeline = []
        cls._data = {}
        cls._pipeline_loaded = False
    
    @classmethod
    def _delete(cls, instance):
        """Delete instance from pipeline (if it's in it), delete instances
        data and cached data
        """
        key = instance._get_key()
        del cls._data[key]
        # Remove instance from pipeline
        while cls._pipeline.count(instance) > 0:
            cls._pipeline.remove(instance)
        delete(key)
    
    def _set_data(self, **kwargs):
        """A generic set data makes no sense since the data may be distributed
        over various data stores, and is not generalizable. So the child
        class has to provide a set() function that stores the data at the
        appropriate place and calls this function
        """
        key = self._get_key()
        if key not in self._data:
            Multiload._pipeline_load()
        for field, data in kwargs.iteritems():
            Multiload._data[key][field] = data
        self._store(self, Multiload._data[key])
    
    def _get_key(self):
        try:
            return self._key
        except AttributeError:
            raise MissingMultiloadAttributeError('self._key')
    
    def has(self, *fields):
        key = self._get_key()
        if key not in Multiload._data:
            Multiload._pipeline_load()
        has = []
        for field in fields:
            has.append(field in Multiload._data[key])
        if len(has) == 1:
            return has[0]
        else:
            return has
        
    def rem(self, *fields):
        """ Removes fields from data and from cache. Accessing a field after
        it was rem'd will result in an error
        """
        key = self._get_key()
        if key not in Multiload._data:
            Multiload._pipeline_load()
        has_fields = self.has(*fields)
        # has_fields will return no list if only one argument was given
        if len(fields) == 1:
            has_fields = [has_fields]
        deleted_fields = []
        for field, has_field in zip(fields, has_fields):
            if has_field:
                del Multiload._data[key][field]
                deleted_fields.append(field)
        Multiload._store(self, Multiload._data[key])
        if len(deleted_fields) > 0 and hasattr(self, '_cb_rem'):
            getattr(self, '_cb_rem')(deleted_fields)
    
    def get(self, *fields):
        """Generic data accessor. Can be overwritten by the child class if
        any kind of processing should be done before the data is returned
        """
        return Multiload._get_data(self, *fields)
    
    def __del__(self):
        """Prevent data leak by removing this instances data from the data
        registry
        """
        try:
            del Multiload._data[self._get_key()]
            if self in Multiload._pipeline:
                Multiload._pipeline.remove(self)
        except:
            pass # Nothing helpful can be done at this point
