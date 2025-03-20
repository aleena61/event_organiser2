from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('add-event/', views.add_event, name='add_event'),
    path('edit-event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('bookmark-event/<int:event_id>/', views.bookmark_event, name='bookmark_event'),
    path('unbookmark-event/<int:event_id>/', views.unbookmark_event, name='unbookmark_event'),
    path('set-reminder/<int:event_id>/', views.set_reminder, name='set_reminder'),
    path('remove-reminder/<int:event_id>/', views.remove_reminder, name='remove_reminder'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/approve-event-edit/<int:event_id>/', views.approve_event_edit, name='approve_event_edit'),
    path('search/', views.search_events, name='search_events'),
    # Password reset URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/<str:email>/', views.verify_otp, name='verify_otp'),
    path('reset-password/<str:email>/', views.reset_password, name='reset_password'),
] 