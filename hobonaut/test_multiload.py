import random
from hobonaut.models import cache
from hobonaut.models import redis_connection
from hobonaut.models.redis_connection import rc, rn


class Test(cache.Multiload):
    def __init__(self, id_):
        self._id = id_
        self._key = 'Test:' + self._id
        super(Test, self).__init__()
        
    def _get_data_all(self):
        data = cc.hgetall(rn(self._id))
        if len(data) == 0:
            raise cache.ObjectNotFoundError(self._id)
        return data
    
    def set(self, **kwargs):
        cc.hmset(rn(self._id), kwargs)
        self._set_data(**kwargs)
        

if __name__ == '__main__':
    redis_connection.set_namespace('testing')
    cc = rc(redis_connection.REDIS_CACHE_DB)
    data = [
            ('testing',
             {
             'a': random.randint(40, 50),
             'b': random.randint(51, 60),
             'c': random.randint(71, 80)
             }
            ),
            ('the_lord',
             {
              'name': 'Lord Testing',
              'county': 'Testingshire',
              'planet': 'Cerebrus XXIV'
             }
            ),
            ('house',
             {
              'color': 'red',
              'location': 'Londonshire',
              'owner': 'Lord Testington',
              'size': '13252sqft',
              'value': '13352267 pounds'
             }
            )
           ]
    
    for key, value in data:
        for subkey, subvalue in value.iteritems():
            cc.hset(rn(key), subkey, subvalue)
            
    list_ = [Test('testing'), Test('the_lord'), Test('house')]
    try:
        int(list_[0].get('a'))
    except:
        print 'First data set failed, returned ' + list_[0].get('a')
    assert list_[1].get('name') == 'Lord Testing', 'Second data set failed,\
                                    returned ' + list_[1].get('name')
    assert list_[2].get('color') == 'red', 'Third data set failed, returned '\
                                            + list_[2].get('color')
    rand1, rand2 = random.randint(90, 99), random.randint(30, 39)
    list_[1].set(one=rand1, two=rand2)
    assert list_[1].get('one') == rand1, 'Data set failure on second\
                                            data set, variable 1'
    assert list_[1].get('two') == rand2, 'Data set failure on second\
                                            data set, variable 2'