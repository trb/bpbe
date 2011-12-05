import redis


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_ARTICLES_DB = 0
REDIS_CACHE_DB = 1
_namespace = 'a'
_redis_connections = {}


def set_namespace(namespace):
    global _namespace
    _namespace = namespace


"""rn = redis_namespace
   Prefixes a key with a namespace. This is done to keep answers/questions
   seperate for different customers
"""
def rn(key):
    return _namespace + ':' + key;


"""Return a redis connection. If none exists, create one first and return that
"""
def rc(db=REDIS_ARTICLES_DB):
    global _redis_connections
    if not db in _redis_connections:
        _redis_connections[db] = redis.StrictRedis(host=REDIS_HOST,
                                                  port=REDIS_PORT,
                                                  db=db)
    return _redis_connections[db]