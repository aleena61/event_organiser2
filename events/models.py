# models.py
from django.db import models

class Event(models.Model):
    name = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField()

    def __str__(self):
        return self.name
    def first_photo_url(self):
        # Get the first photo URL if exists, else return a placeholder image URL
        first_photo = self.photos.first()
        if first_photo:  # If a photo exists, return its URL
            return first_photo.image.url
        return '/static/images/event2.jpg' 

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
