
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from events import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
   
    path('calendar/', views.calendar_view, name='calendar'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('add_event/', views.add_event, name='add-event'),
    path('create_newsletter/<int:event_id>/', views.create_newsletter, name='create_newsletter'),
   



    path('signup/', views.signup_view, name='signup'),
    path('login_view/', views.login_view, name='login_view'),
    # Add other paths as needed

    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout_view'),
    path('', views.home, name='home'),
    path('bookmark/<int:event_id>/', views.bookmark_event, name='bookmark_event'),
    path('bookmarked-events/', views.bookmarked_events, name='bookmarked_events'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

