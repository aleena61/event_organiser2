# models.py
from django.db import models
from django.contrib.auth.models import User


    

class Event(models.Model):

    CATEGORY_CHOICES = [
        ('cultural', 'Cultural'),
        ('Music', 'Music'),
        ('Sports', 'Sports'),
        ('Art', 'Art'),
        ('Tech', 'Tech'),
        ('Food', 'Food'),
    ]

    name = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField()
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    newsletter = models.TextField(blank=True, null=True)  # Newsletter field
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='cultural')
    visits = models.IntegerField(default=0)  # New field to track event visits
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")  # Link event to user
    bookmarked_by = models.ManyToManyField(User, related_name="bookmarked_events", blank=True)

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    requested_approval = models.BooleanField(default=False)
    delete_requested = models.BooleanField(default=False)
    def __str__(self):
        return self.name
    def first_photo_url(self):
        # Get the first photo URL if exists, else return a placeholder image URL
        first_photo = self.photos.first()
        if first_photo:  # If a photo exists, return its URL
            return first_photo.image.url
        return '/static/images/event2.jpg' 
class UserCalendar(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)  # When the event was added to the calendar
    
    def __str__(self):
        return f"{self.event.name} on {self.event.date}"

class EventPhoto(models.Model):
    event = models.ForeignKey(Event, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='events/photos/')

    def __str__(self):
        return f"Photo for {self.event.name}"

class OldPhoto(models.Model):
    event = models.ForeignKey(Event, related_name='old_photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='events/old_photos/')

    def __str__(self):
        return f"Old Photo for {self.event.name}"

class Competition(models.Model):
    event = models.ForeignKey(Event, related_name='competitions', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date = models.DateField()
    place = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

    
 

    
