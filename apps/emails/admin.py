from django.contrib import admin
from .models import EmailTemplate, EmailLog, NewsletterSubscription, EmailCampaign

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name','template_type','is_active']
    list_filter = ['template_type','is_active']

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient','subject','status','created_at','sent_at']
    list_filter = ['status','created_at']
    search_fields = ['recipient','subject']

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email','is_active','subscribed_at']
    list_filter = ['is_active','subscribed_at']
    search_fields = ['email']

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['name','status','total_recipients','sent_count','failed_count','scheduled_at']
    list_filter = ['status','created_at']
    search_fields = ['name','subject']
    readonly_fields = ['total_recipients','sent_count','failed_count','sent_at']
