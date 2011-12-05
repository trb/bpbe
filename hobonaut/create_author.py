from hobonaut.models.redis_connection import rc, rn

author = {
  'id': '1',
  'name': 'hobo',
  'email': 'thomas.rubbert@yahoo.de',
  'password_hash': '98be6395d8c4e75aa057f7b5bcaaca759f191b2d26ed3f9ac44668c434513075774e491f39c58d5caa41e832dee80f9d788b7d29336a9b689e12ab4ee68ddaef',
  'password_salt': '2Bpuemtj9wMCKfOdYWdP'
}

rc().hmset(rn('author:{0}'.format(author['id'])), author)

rc().set(rn('author:name_to_id:{0}'.format(author['name'])), author['id'])

rc().sadd(rn('authors'), author['id'])
