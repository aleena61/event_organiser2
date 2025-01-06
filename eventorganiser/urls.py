
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
    path('dashboard/', views.event_dashboard, name='event_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout_view'),
    path('', views.home, name='home'),
    path('bookmark/<int:event_id>/', views.bookmark_event, name='bookmark_event'),
    path('bookmarked-events/', views.bookmarked_events, name='bookmarked_events'),
    path('event/edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('check-login-status/', views.check_login_status, name='check_login_status'),
   
     path('update_location/', views.update_location, name='update_location'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

