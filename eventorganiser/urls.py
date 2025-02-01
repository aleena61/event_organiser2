
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
   
    path('dashboard/', views.dashboard_view, name='dashboard_view_admin'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('add_event/', views.add_event, name='add-event'),
    path('create_newsletter/<int:event_id>/', views.create_newsletter, name='create_newsletter'),
    path('signup/', views.signup_view, name='signup'),
    path('login_view/', views.login_view, name='login_view'),
    # Add other paths as needed
    path('dashboardevent/', views.event_dashboard, name='event_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout_view'),
    path('', views.home, name='home'),
    path('bookmark/<int:event_id>/', views.bookmark_event, name='bookmark_event'),
    path('bookmarked-events/', views.bookmarked_events, name='bookmarked_events'),
    path('event/edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('check-login-status/', views.check_login_status, name='check_login_status'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('update_location/', views.update_location, name='update_location'),
     path('approve_events/', views.approve_events, name='approve_events'),
    path('reject_events/', views.reject_events, name='reject_events'),
    path('approve_changes/', views.approve_changes, name='approve_changes'),
    path('reject_changes/', views.reject_changes, name='reject_changes'),
    path('approve_deletion/', views.approve_deletion, name='approve_deletion'),
    path('reject_deletion/', views.reject_deletion, name='reject_deletion'),
    path('manage_events/', views.manage_events, name='manage_events'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

