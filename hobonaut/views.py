from models.redis_connection import rn, rc
from models import generic_data
from models import articles, authors
from models import slogan
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
import os
import base64
import time
import re
import datetime
import random
import hashlib


def date_format(format, timestamp):
    """@todo Create utility system that is available in templates, move this
          function there
    """
    return time.strftime(format, time.localtime(float(timestamp)))


def generate_id():
    return base64.urlsafe_b64encode(os.urandom(12))


def display_articles(request):
    return {
            'articles': articles.get_published(),
            'slogan': slogan.get()
            }


def admin(request):
    return {
            'time': time,
            'date_format': date_format,
            'public_articles': articles.get_published(max_=None),
            'scheduled_articles': articles.get_scheduled(),
            'private_articles': articles.get_private(),
            'slogan': slogan.get()
            }


def write_article(request):
    return {}


def edit_article(request):
    article = articles.get(request.matchdict['id'])
    
    if article.has('publish_at'):
        publish_at = article.get('publish_at')
    else:
        publish_at = None
        
    return {
            'editing': True,
            'id': article.get('id'),
            'text': article.get('text'),
            'text_compiled': article.get('text_compiled'),
            'title': article.get('title'),
            'tldr': article.get('tldr'),
            'updated_at': article.get('updated_at'),
            'publish_at': publish_at,
            'is_published': article.is_published(),
            'is_scheduled': article.is_scheduled(),
            'date_format': date_format
            }


def new_article_id(request):
    article_id = generate_id()
    # zscore is O(1), zrank is O(log(n)), both return None if key doesn't exist
    while rc().zscore(rn('articles'), article_id) is not None:
        article_id = generate_id()
    
    return {
            'article_id': article_id
            }

    
def save_article(request):
    us_article_id = request.matchdict['id']
    article = articles.get(us_article_id)
    save_data = {}
    for us_key, us_value in request.POST.items():
        """Only auto-save fields with the article-prefix to keep
        junk from entering the article-hash
        """
        if us_key[:8] == 'article-':
            save_data[us_key[8:]] = us_value
    article.set(**save_data)

    
def confirm_article_deletion(request):
    article_id = request.matchdict['id']
    article = articles.get(article_id)
    return {
            'id': article.get('id'),
            'title': article.get('title'),
            'margin_left': str(random.randint(0, 85)),
            'margin_top': str(random.randint(5, 25))
            }

    
def delete_article(request):
    us_article_id = request.matchdict['id']
    article = articles.get(us_article_id)
    article.delete()
    return HTTPFound(location='/admin')


def publish_article(request):
    us_article_id = request.matchdict['id']
    article = articles.get(us_article_id)
    article.publish()
    
    
def unpublish_article(request):
    us_article_id = request.matchdict['id']
    article = articles.get(us_article_id)
    article.unpublish()
    
    
def schedule_article(request):
    us_article_id = request.matchdict['id']
    us_date = request.POST.get('date')
    match = re.match('(\d\d)/(\d\d)/(\d\d\d\d)\s(\d\d):(\d\d)',
                     us_date,
                     flags=re.IGNORECASE)
    month, day, year, hour, minute = match.groups()
    dt = datetime.datetime(int(year), int(month), int(day), int(hour),
                           int(minute))
    timestamp = time.mktime(dt.timetuple())
    article = articles.get(us_article_id)
    article.schedule(timestamp)


def slogan_save(request):
    slogan.save(request.POST.get('slogan'))


def login(request):
    us_name = request.POST.get('name')
    us_password = request.POST.get('password')
    redirect = None
    try:
        author = authors.get_by_name(us_name)
        
        if author.verify(us_password):
            redirect = HTTPFound(location=request.route_url('admin'),
                                 headers=remember(request, author.get('name')))
        else:
            redirect = HTTPFound(location=request.route_url('login'))
    except:
        #redirect = HTTPFound(location='/admin/write')
        redirect = HTTPFound(location=request.route_url('login'))
        
    return redirect


def error_forbidden(request):
    return {}


def redis(request):
    key_search = '*'
    if 'search' in request.GET:
        us_key_search = request.GET['search']
        if re.match('^[a-zA-Z0-9\-_:]+$', us_key_search):
            key_search = us_key_search
    kwargs = {}
    if 'db' in request.GET:
        if re.match('[0-9]{1,2}', str(request.GET['db'])):
            kwargs['db'] = int(request.GET['db'])
    
    data = generic_data.GenericData(key_search, **kwargs)
    
    return {
            'request': request,
            'values': data.get_all()
            }