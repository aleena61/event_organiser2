from django.contrib import admin
from django.contrib.auth.models import User
from .models import Event, Competition,EventUser,Notification


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'delete_requested')  # Use 'name' instead of 'title'
    list_filter = ('status',)
    actions = ['approve_deletion', 'reject_deletion', 'approve_changes', 'reject_changes', 'approve_events']

    def save_model(self, request, obj, form, change):
        """
        Overrides the save_model method to create a notification
        for the superuser when a new event submission is created.
        """
        if not change:  # Check if this is a new object (not an update)
            superusers = User.objects.filter(is_superuser=True)
            for superuser in superusers:
                Notification.objects.create(
                    user=superuser,
                    message=f"A new event submission '{obj.name}' has been created."
                )
        super().save_model(request, obj, form, change)

    
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
admin.site.register(EventUser)


from django.contrib.admin import AdminSite


class CustomAdminSite(AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        return context

admin_site = CustomAdminSite()
