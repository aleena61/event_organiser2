from django.contrib import admin
from .models import Event, Competition
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'status')
    list_filter = ('status',)
    actions = ['approve_events']

    def approve_events(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, "Selected events have been approved.")
    approve_events.short_description = "Approve selected events"

# Register your models here.
admin.site.register(Event,EventAdmin)
admin.site.register(Competition)