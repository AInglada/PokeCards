from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger=logging.getLogger(__name__)

class EmailTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES=[
        ('welcome',_('Welcome Email')),('order_confirmation',_('Order Confirmation')),
        ('order_shipped',_('Order Shipped')),('order_delivered',_('Order Delivered')),
        ('password_reset',_('Password Reset')),('newsletter',_('Newsletter')),
        ('promotional',_('Promotional')),('low_stock_alert',_('Low Stock Alert')),
        ('invoice',_('Invoice'))
    ]
    name=models.CharField(_('name'),max_length=100)
    template_type=models.CharField(_('template type'),max_length=50,choices=TEMPLATE_TYPE_CHOICES,unique=True)
    subject=models.CharField(_('subject'),max_length=200)
    html_content=models.TextField(_('HTML content'))
    text_content=models.TextField(_('text content'),blank=True)
    available_variables=models.JSONField(_('available variables'),default=dict,
        help_text=_('Variables for template'))
    is_active=models.BooleanField(_('active'),default=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)

    class Meta:
        verbose_name=_('email template'); verbose_name_plural=_('email templates')

    def __str__(self): return self.name

class EmailLog(models.Model):
    STATUS_CHOICES=[('pending',_('Pending')),('sent',_('Sent')),('failed',_('Failed'))]
    template=models.ForeignKey(EmailTemplate,on_delete=models.SET_NULL,null=True,blank=True,
                               related_name='email_logs',verbose_name=_('template'))
    recipient=models.EmailField(_('recipient'))
    subject=models.CharField(_('subject'),max_length=200)
    status=models.CharField(_('status'),max_length=20,choices=STATUS_CHOICES,default='pending')
    error_message=models.TextField(_('error message'),blank=True)
    metadata=models.JSONField(_('metadata'),default=dict,blank=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    sent_at=models.DateTimeField(_('sent at'),null=True,blank=True)

    class Meta:
        verbose_name=_('email log'); verbose_name_plural=_('email logs'); ordering=['-created_at']

    def __str__(self): return f"{self.recipient} – {self.subject}"

class NewsletterSubscription(models.Model):
    email=models.EmailField(_('email'),unique=True)
    user=models.OneToOneField('accounts.User',on_delete=models.SET_NULL,null=True,blank=True,
                              related_name='newsletter_subscription',verbose_name=_('user'))
    is_active=models.BooleanField(_('active'),default=True)
    subscribed_at=models.DateTimeField(_('subscribed at'),auto_now_add=True)
    unsubscribed_at=models.DateTimeField(_('unsubscribed at'),null=True,blank=True)

    class Meta:
        verbose_name=_('newsletter subscription'); verbose_name_plural=_('newsletter subscriptions'); ordering=['-subscribed_at']

    def __str__(self): return self.email

class EmailCampaign(models.Model):
    STATUS_CHOICES=[('draft',_('Draft')),('scheduled',_('Scheduled')),
                    ('sending',_('Sending')),('sent',_('Sent')),('cancelled',_('Cancelled'))]
    name=models.CharField(_('name'),max_length=200)
    subject=models.CharField(_('subject'),max_length=200)
    html_content=models.TextField(_('HTML content'))
    text_content=models.TextField(_('text content'),blank=True)
    send_to_all_subscribers=models.BooleanField(_('send to all subscribers'),default=False)
    specific_recipients=models.ManyToManyField('accounts.User',blank=True,
                                               related_name='email_campaigns',verbose_name=_('specific recipients'))
    status=models.CharField(_('status'),max_length=20,choices=STATUS_CHOICES,default='draft')
    scheduled_at=models.DateTimeField(_('scheduled at'),null=True,blank=True)
    total_recipients=models.IntegerField(_('total recipients'),default=0)
    sent_count=models.IntegerField(_('sent count'),default=0)
    failed_count=models.IntegerField(_('failed count'),default=0)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)
    sent_at=models.DateTimeField(_('sent at'),null=True,blank=True)

    class Meta:
        verbose_name=_('email campaign'); verbose_name_plural=_('email campaigns'); ordering=['-created_at']

    def __str__(self): return self.name

class EmailService:
    @staticmethod
    def send_email(to_email, subject, html_content, text_content=None, template_type=None, context=None, attachments=None):
        email_log=None
        try:
            from .models import EmailLog, EmailTemplate
            email_log=EmailLog.objects.create(recipient=to_email,subject=subject,metadata={'context':context} if context else {})
            if template_type:
                try:
                    template=EmailTemplate.objects.get(template_type=template_type,is_active=True)
                    email_log.template=template; subject=template.subject
                    if context:
                        html_content=render_to_string('emails/base.html',{'content':template.html_content,**context})
                except EmailTemplate.DoesNotExist:
                    logger.warning(f"Template not found: {template_type}")
            msg=EmailMultiAlternatives(subject=subject,body=text_content or html_content,
                                      from_email=settings.DEFAULT_FROM_EMAIL,to=[to_email])
            msg.attach_alternative(html_content,"text/html")
            if attachments:
                for path in attachments: msg.attach_file(path)
            msg.send()
            from django.utils import timezone
            email_log.status='sent'; email_log.sent_at=timezone.now(); email_log.save()
            return True,email_log
        except Exception as e:
            logger.error(f"Email failed to {to_email}: {e}")
            if email_log:
                email_log.status='failed'; email_log.error_message=str(e); email_log.save()
            return False,email_log
