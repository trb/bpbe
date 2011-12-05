from redis_connection import *
import redis


class GenericData:
    key_Search = '*'
    connection = None
    
    def __init__(self, key_search, db = REDIS_ARTICLES_DB):
        self.key_search = key_search
        self.connection = redis.StrictRedis(db=db)

    def get_type_string(self, key):
        return self.connection.get(key)
        
    def get_type_zset(self, key):
        values = self.connection.zrange(key, 0, -1, withscores=True)
        representation = ''
        for value, score in values:
            representation+= str(value) + ' (' + str(score) + '), '
        representation = representation[:-2]
        return representation
    
    def get_type_set(self, key):
        values = self.connection.smembers(key)
        representation = ''
        for value in values:
            representation+= value + ', '
        representation = representation[:-2]
        return representation
    
    def get_type_list(self, key):
        values = self.connection.lrange(key, 0, -1)
        representation = ''
        for value in values:
            representation+= value + '-'
        representation = representation[:-1]
        return representation
    
    def get_type_hash(self, key):
        values = self.connection.hgetall(key)
        representation = ''
        for field, value in values.iteritems():
            representation+= field + ' => ' + value + '\n'
        return representation

        
    def get_all(self):
        keys_count = self.connection.dbsize()
        if keys_count > 2000:
            raise Exception('Too many keys to display (10000+)')
        # Gets all keys (wildcard) in order
        keys = sorted(self.connection.keys(self.key_search))
        values = dict()
        for key in keys:
            type = self.connection.type(key).lower()
            values[key] = getattr(self, 'get_type_' + type)(key)
        return values
            
            
        
        