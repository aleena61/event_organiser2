from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Event, Notification
from django.contrib.auth.models import User
from django.apps import apps

@receiver(post_save, sender=Event)
def event_updated_notification(sender, instance, created, **kwargs):
    if not created:  # Notify attendees if event date is updated
        attendees = instance.attendees.all()
        for attendee in attendees:
            Notification.objects.create(
                user=attendee,
                message=f"The event '{instance.name}' has been rescheduled to {instance.date}."
            )

@receiver(post_save, sender=Event)
def event_submission_notification(sender, instance, created, **kwargs):
    if created:  # Notify admin on new event submission
        auth_user = User.objects.filter(is_staff=True)
        for admin in auth_user:
            Notification.objects.create(
                user=admin,
                message=f"New event '{instance.name}' submitted by {instance.coordinator.username}."
            )