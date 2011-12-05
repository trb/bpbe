from hobonaut.models.redis_connection import rc, rn
from hobonaut import resources


class AuthorNotFoundError(Exception):
    def __init__(self, id_):
        self._id = id_
        
    def __str__(self):
        return 'Author with id "', self._id, 'was not found'


def get(id_):
    if not rc().sismember(rn('authors'), id_):
        raise AuthorNotFoundError(id_)
    
    return Author(id_)


def get_by_name(name):
    id_ = rc().get(rn('author:name_to_id:{0}'.format(name)))
    
    return get(id_)


class Author(object):
    def __init__(self, id_):
        self._id = id_
        self._data = None

    def _get_data(self):
        self._data = rc().hgetall(rn('author:{0}'.format(self._id)))

    def get(self, field):
        if self._data is None:
            self._get_data()
            
        return self._data[field]
    
    def verify(self, password):
        password_hash = resources.hash(resources.global_salt,
                              self.get('password_salt'),
                              password)
        return password_hash == self.get('password_hash')
