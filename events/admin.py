from django.contrib import admin
from .models import Event, Competition

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'delete_requested')  # Use 'name' instead of 'title'
    list_filter = ('status',)
    actions = ['approve_deletion', 'reject_deletion', 'approve_changes', 'reject_changes', 'approve_events']

    def approve_deletion(self, request, queryset):
        queryset.update(delete_requested=False, status='deleted')
        for event in queryset:
            event.delete()
    approve_deletion.short_description = "Approve selected events' deletion"

    def reject_deletion(self, request, queryset):
        queryset.update(delete_requested=False, status='active')
    reject_deletion.short_description = "Reject selected events' deletion"

    def approve_changes(self, request, queryset):
        queryset.update(requested_approval=False, status='approved')
    approve_changes.short_description = "Approve selected events' changes"

    def reject_changes(self, request, queryset):
        queryset.update(requested_approval=False, status='rejected')
    reject_changes.short_description = "Reject selected events' changes"

    def approve_events(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, "Selected events have been approved.")
    approve_events.short_description = "Approve selected events"

# Register the Competition model
admin.site.register(Competition)
