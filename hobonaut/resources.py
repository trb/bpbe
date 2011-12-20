from pyramid.security import Allow, DENY_ALL
import hashlib


global_salt = 'B6Wo3wQFYoTpZLEE_BB-q-_D'


def hash(global_salt, user_salt, user_password):
    """Apply the custom hash scheme:
    
    sha512 of global salt, user specific salt (stored in db), and password
    """
    h = hashlib.sha512()
    h.update(global_salt)
    h.update(user_salt)
    h.update(user_password)
    
    return h.hexdigest()


class Root(object):
    def __init__(self, request):
        self.request = request


class Backend(object):
    __acl__ = [
               (Allow, 'hobo', 'view'),
               (Allow, 'hobo', 'edit'),
               DENY_ALL
               ]
    
    def __init__(self, request):
        self.request = request
