from django.contrib import admin
from .models import Event, Competition


# Register your models here.
admin.site.register(Event)
admin.site.register(Competition)