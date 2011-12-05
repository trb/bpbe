from hobonaut.models.redis_connection import rn, rc
from hobonaut.models import articles
import time


if __name__ == '__main__':
    last_run = rc().get(rn('pipeline:last_run'))
    if last_run is None:
        last_run = '-inf'
    now = int(time.time())
    publishable_articles = rc().zrevrangebyscore(rn('pipeline'), now, last_run)
    for article_id in publishable_articles:
        article = articles.get(article_id)
        article.publish()
        rc().zrem(rn('pipeline'), article_id)
    rc().set(rn('pipeline:last_run'), now)