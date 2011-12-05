from hobonaut.models.redis_connection import rc, rn
from hobonaut.models import cache
import time
import markdown


def mget(*ids):
    """Return one Article, specified by id
    
    Does not use the cache, don't use for performance intensive cases
    
    @param id: Id of article
    @return hobonaut.models.articles.Article
    """
    articles = []
    for id_ in ids:
        articles.append(Article(id_))
    return articles


def get(id_):
    return mget(id_)[0]
    
    
def clear_published_articles():
    cache.delete('articles')


def get_published(max_ = 7):
    """Get articles that were published, at most "max"
    
    Tries to load articles from cache for maximum performance, only creates
    Article's when cache misses
    
    @param max: The maximum number of articles returned
    @return list of Article's
    """
    def get_articles(max_):
        # -1 denotes the last entry in redis sets, 0 to -1 = all
        if max_ is None:
            max_ = -1
        return rc().zrevrange(rn('articles:published'), 0, max_)
    article_ids = cache.read('articles', get_articles, [max_])
    return mget(*article_ids)


def get_private():
    """Returns a list of articles that are neither published, nor scheduled,
    and therefore private
    """
    
    """Intersecting three sets with 10M entries each takes about 75s in python,
    so simply read all articles, published articles and pipeline from redis and
    diff those in python
    """
    articles = set(rc().zrevrange(rn('articles'), 0, -1))
    published = set(rc().zrevrange(rn('articles:published'), 0, -1))
    scheduled = set(rc().zrevrange(rn('pipeline'), 0, -1))
    article_ids = articles - published - scheduled
    
    return mget(*article_ids)


def get_scheduled():
    """Returns a list of Article's that were written and scheduled for
    publication sometime in the future
    """
    article_ids = rc().zrevrange(rn('pipeline'), 0, -1)
    return mget(*article_ids)


class Article(cache.Multiload):
    def __init__(self, id_):
        self._id = id_
        self._key = 'Article:' + str(self._id)
        super(Article, self).__init__()
        
    def _get_data_all(self):
        pipeline = rc().pipeline()
        pipeline.hgetall(rn('article:{0}'.format(self._id)))\
            .get(rn('article:{0}:last_retrieval_at'.format(self._id)))\
            .zincrby(rn('articles:times_retrieved'), self._id, 1)\
            .set(rn('article:{0}:last_retrieval_at'.format(self._id)),
                 int(time.time()))
        data = pipeline.execute()
        return_data = data[0]
        return_data['last_retrieval_at'] = data[1]
        
        return return_data
        
    def _title_url(self, title):
        clean_title = ''
        title = title.lower()
        for c in title:
            if c == ' ':
                clean_title+= '-'
            if c in 'abcdefghijklmnopqrstuvwxyz1234567890_,.!':
                clean_title+= c
                
        return clean_title
    
    def exists(self):
        """zscore is faster than zrank"""
        return rc().zscore(rn('articles'), self._id) is not None
    
    def create(self):
        """Creates initial values for an article"""
        now = int(time.time())
        rc().zadd(rn('articles'), now, self._id)
        rc().hmset(rn('article:{0}'.format(self._id)),
                   {
                    'created_at': now,
                    'id': self._id
                    })
        
    def set(self, **data):
        """Saves given key=value pairs and updates cache
        """
        if not self.exists():
            self.create()
        save_data = {}
        save_data['updated_at'] = int(time.time())
        for key, value in data.iteritems():
            """Special cases that require more actions than just adding
            them to the article hash
            """
            if key == 'author':
                # remove previous author
                if 'author' in self._data:
                    key = 'author:{0}:articles'.format(self._data['author'])
                    rc().srem(rn(key), self._id)
                rc().sadd(rn('author:{0}:articles'.format(key)), self._id)
            if key == 'title':
                if self.has('title'):
                    old_url_title = self._title_url(self.get('title'))
                    rc().delete(rn('article:title_to_id:{0}'\
                                   .format(old_url_title)))
                url_title = self._title_url(value)
                if len(url_title) > 0:
                    rc().set(rn('article:title_to_id:{0}'.format(url_title)),
                             self._id)
            if key == 'text':
                save_data['text_compiled'] = markdown.markdown(value)
            save_data[key] = value
        rc().hmset(rn('article:{0}'.format(self._id)), save_data)
        self._set_data(**save_data)
        
    def delete(self):
        if not self.exists():
            return # My work here is done
        
        pipeline = rc().pipeline()
        url_title = self._title_url(self.get('title'))
        pipeline.delete(rn('article:title_to_id:{0}'.format(url_title)))\
            .delete(rn('article:{0}'.format(self._id)))\
            .delete(rn('article:{0}:last_retrieval_at'.format(self._id)))\
            .zrem(rn('articles'), self._id)\
            .zrem(rn('articles:published'), self._id)\
            .zrem(rn('articles:times_retrieved'), self._id)\
            .zrem(rn('pipeline'), self._id)
        pipeline.execute()
        clear_published_articles()
        self._delete(self)
        
    def _cb_rem(self, fields):
        """ Delete fields from article hash """
        for field in fields:
            rc().hdel(rn('article:{0}'.format(self._id)), field)
        
    def is_published(self):
        return rc().zscore(rn('articles:published'), self._id) is not None
    
    def is_scheduled(self):
        return rc().zscore(rn('pipeline'), self._id) is not None
        
    def publish(self):
        if self.has('publish_at'):
            publish_at = self.get('publish_at')
        else:
            publish_at = int(time.time())
        rc().zadd(rn('articles:published'), publish_at, self._id)
        self.set(publish_at=publish_at)
        clear_published_articles()
        
    def unpublish(self):
        rc().zrem(rn('articles:published'), self._id)
        if self.has('publish_at'):
            self.rem('publish_at')
        clear_published_articles()
        
    def schedule(self, timestamp):
        rc().zadd(rn('pipeline'), timestamp, self._id)
        self.set(publish_at=timestamp)
