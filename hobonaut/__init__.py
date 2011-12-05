from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.httpexceptions import HTTPForbidden

from hobonaut.resources import Root, Backend
from hobonaut.models import authors

import views
import jinja2_filters

def main(global_config, **settings):
    secret = 'mH9o43VCtnq7sD40KC3R'
    """ This function returns a Pyramid WSGI application.
    """
    session = UnencryptedCookieSessionFactoryConfig(secret)
    authentication_policy = AuthTktAuthenticationPolicy(secret,
                                                        timeout=600)
    authorization_policy = ACLAuthorizationPolicy()
    config = Configurator(root_factory=Root,
                          session_factory=session,
                          authentication_policy=authentication_policy,
                          authorization_policy=authorization_policy,
                          settings=settings)
    config.include('pyramid_jinja2')
    config.add_subscriber('hobonaut.event_handlers.set_session_id',
                          'pyramid.events.NewRequest')
    
    config.add_subscriber('hobonaut.event_handlers.cleanup',
                          'pyramid.events.NewRequest')
    """Jinja2 custom filters
    """
    jinja2_filters.register_all(config.get_jinja2_environment())
    
    config.add_route('display_articles', '/')
    config.add_route('login', '/login')
    config.add_route('admin', '/admin',
                     factory='hobonaut.resources.Backend')
    config.add_route('new_article_id', '/admin/new_article_id',
                     factory='hobonaut.resources.Backend')
    config.add_route('write', '/admin/write',
                     factory='hobonaut.resources.Backend')
    config.add_route('article', '/admin/article/{id}',
                     factory='hobonaut.resources.Backend')
    config.add_route('delete', '/admin/article/{id}/delete',
                     factory='hobonaut.resources.Backend')
    config.add_route('publish', '/admin/article/{id}/publish',
                     factory='hobonaut.resources.Backend')
    config.add_route('unpublish', '/admin/article/{id}/unpublish',
                     factory='hobonaut.resources.Backend')
    config.add_route('schedule', '/admin/article/{id}/schedule',
                     factory='hobonaut.resources.Backend')
    config.add_route('slogan', '/admin/slogan',
                     factory='hobonaut.resources.Backend')
    config.add_route('redis', '/redis',
                     factory='hobonaut.resources.Backend')
    
    # Only for testing/developing purposes, should be deactivted in prod.
    config.add_view('hobonaut.views.redis',
                    route_name='redis',
                    renderer='hobonaut:templates/redis.jinja2')
    
    # Error pages
    config.add_view('hobonaut.views.error_forbidden',
                    context=HTTPForbidden,
                    renderer='hobonaut:templates/errors/forbidden.jinja2')
    
    config.add_view('hobonaut.views.display_articles',
                    route_name='display_articles',
                    renderer='hobonaut:templates/articles.jinja2')
    config.add_view('hobonaut.views.error_forbidden',
                    route_name='login',
                    renderer='hobonaut:templates/errors/forbidden.jinja2',
                    request_method='GET')
    config.add_view('hobonaut.views.login',
                    route_name='login',
                    request_method='POST')
    config.add_view('hobonaut.views.admin',
                    route_name='admin',
                    renderer='hobonaut:templates/admin/controlpanel.jinja2',
                    permission='view')
    config.add_view('hobonaut.views.new_article_id',
                    route_name='new_article_id',
                    renderer='json',
                    permission='edit')
    config.add_view('hobonaut.views.write_article',
                    route_name='write',
                    renderer='hobonaut:templates/admin/article.jinja2',
                    permission='view')
    config.add_view('hobonaut.views.edit_article',
                    route_name='article',
                    renderer='hobonaut:templates/admin/article.jinja2',
                    request_method='GET',
                    permission='view')
    config.add_view('hobonaut.views.save_article',
                    route_name='article',
                    renderer='json',
                    request_method='POST',
                    permission='edit')
    config.add_view('hobonaut.views.confirm_article_deletion',
                    route_name='delete',
                    renderer='hobonaut:templates/admin/delete_article.jinja2',
                    request_method='GET',
                    permission='view')
    config.add_view('hobonaut.views.delete_article',
                    route_name='delete',
                    renderer='json',
                    request_method='POST')
    config.add_view('hobonaut.views.publish_article',
                    route_name='publish',
                    renderer='json',
                    request_method='POST',
                    permission='edit')
    config.add_view('hobonaut.views.unpublish_article',
                    route_name='unpublish',
                    renderer='json',
                    request_method='POST',
                    permission='edit')
    config.add_view('hobonaut.views.schedule_article',
                    route_name='schedule',
                    renderer='json',
                    request_method='POST',
                    permission='edit')
    config.add_view('hobonaut.views.slogan_save',
                    route_name='slogan',
                    renderer='json',
                    request_method='POST',
                    permission='edit')
    config.add_static_view('static', 'hobonaut:static')
    
    return config.make_wsgi_app()

