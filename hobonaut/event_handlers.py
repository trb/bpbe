import views
import models.cache

def set_session_id(event):
    if not 'u_id' in event.request.session:
        event.request.session['u_id'] = views.generate_id()
        
        
def cleanup(event):
    if event.request.path[:7] != '/static':
        event.request.add_finished_callback(models.cache.Multiload.cleanup)