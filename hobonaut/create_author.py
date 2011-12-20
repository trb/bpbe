from hobonaut.models.redis_connection import rc, rn

author = {
  'id': '1',
  'name': 'some_author',
  'email': 'author@example.com',
  'password_hash': '',
  'password_salt': ''
}

rc().hmset(rn('author:{0}'.format(author['id'])), author)

rc().set(rn('author:name_to_id:{0}'.format(author['name'])), author['id'])

rc().sadd(rn('authors'), author['id'])
