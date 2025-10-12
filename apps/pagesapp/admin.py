# apps/pagesapp/admin.py
from django.contrib import admin
from .models import Banner, Article


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    list_editable = ['priority', 'active']
    search_fields = ['title', 'subtitle']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subtitle', 'image_url', 'link_url')
        }),
        ('Display Settings', {
            'fields': ('priority', 'active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'published', 'published_at', 'created_at']
    list_filter = ['published', 'published_at']
    search_fields = ['title', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'summary', 'content', 'image_url')
        }),
        ('Publication', {
            'fields': ('published', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

