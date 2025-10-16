from django.contrib import admin
from .models import SystemAlert, DashboardWidget

@admin.register(SystemAlert)
class SystemAlertAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'alert_type', 'priority', 'is_read', 
        'is_resolved', 'created_at'
    ]
    list_filter = [
        'alert_type', 'priority', 'is_read', 
        'is_resolved', 'created_at'
    ]
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    
    actions = ['mark_as_read', 'mark_as_resolved']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected alerts as read"
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True, resolved_by=request.user, resolved_at=timezone.now())
    mark_as_resolved.short_description = "Mark selected alerts as resolved"


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'widget_type', 'position', 'is_visible', 'size']
    list_filter = ['widget_type', 'is_visible', 'size']
    search_fields = ['user__email']
