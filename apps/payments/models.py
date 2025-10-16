from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.accounts.models import User
from apps.orders.models import Order

class PaymentGateway(models.Model):
    GATEWAY_CHOICES=[('paypal',_('PayPal')),('stripe',_('Stripe')),('square',_('Square')),('manual',_('Manual/Bank Transfer'))]
    name=models.CharField(_('name'),max_length=50,choices=GATEWAY_CHOICES,unique=True)
    display_name=models.CharField(_('display name'),max_length=100)
    is_active=models.BooleanField(_('active'),default=True)
    is_test_mode=models.BooleanField(_('test mode'),default=True)
    order=models.IntegerField(_('order'),default=0)
    config=models.JSONField(_('configuration'),default=dict,blank=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)

    class Meta:
        verbose_name=_('payment gateway'); verbose_name_plural=_('payment gateways'); ordering=['order','name']

    def __str__(self): return self.display_name

class Payment(models.Model):
    STATUS_CHOICES=[('pending',_('Pending')),('processing',_('Processing')),('completed',_('Completed')),('failed',_('Failed')),('cancelled',_('Cancelled')),('refunded',_('Refunded')),('partially_refunded',_('Partially Refunded'))]
    transaction_id=models.CharField(_('transaction ID'),max_length=100,unique=True)
    gateway_transaction_id=models.CharField(_('gateway transaction ID'),max_length=255,blank=True)
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='payments',verbose_name=_('order'))
    gateway=models.ForeignKey(PaymentGateway,on_delete=models.SET_NULL,null=True,verbose_name=_('payment gateway'))
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='payments',verbose_name=_('user'))
    amount=models.DecimalField(_('amount'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    currency=models.CharField(_('currency'),max_length=3,default='USD')
    status=models.CharField(_('status'),max_length=20,choices=STATUS_CHOICES,default='pending')
    gateway_response=models.JSONField(_('gateway response'),default=dict,blank=True)
    notes=models.TextField(_('notes'),blank=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)
    completed_at=models.DateTimeField(_('completed at'),null=True,blank=True)

    class Meta:
        verbose_name=_('payment'); verbose_name_plural=_('payments'); ordering=['-created_at']

    def __str__(self): return f"Payment {self.transaction_id} – {self.status}"

class Refund(models.Model):
    STATUS_CHOICES=[('pending',_('Pending')),('processing',_('Processing')),('completed',_('Completed')),('failed',_('Failed'))]
    REASON_CHOICES=[('customer_request',_('Customer Request')),('duplicate',_('Duplicate Payment')),('fraudulent',_('Fraudulent')),('product_issue',_('Product Issue')),('other',_('Other'))]
    refund_id=models.CharField(_('refund ID'),max_length=100,unique=True)
    gateway_refund_id=models.CharField(_('gateway refund ID'),max_length=255,blank=True)
    payment=models.ForeignKey(Payment,on_delete=models.CASCADE,related_name='refunds',verbose_name=_('payment'))
    processed_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='processed_refunds',verbose_name=_('processed by'))
    amount=models.DecimalField(_('amount'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))])
    reason=models.CharField(_('reason'),max_length=20,choices=REASON_CHOICES)
    status=models.CharField(_('status'),max_length=20,choices=STATUS_CHOICES,default='pending')
    notes=models.TextField(_('notes'),blank=True)
    gateway_response=models.JSONField(_('gateway response'),default=dict,blank=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)
    completed_at=models.DateTimeField(_('completed at'),null=True,blank=True)

    class Meta:
        verbose_name=_('refund'); verbose_name_plural=_('refunds'); ordering=['-created_at']

    def __str__(self): return f"Refund {self.refund_id} – {self.amount}"
