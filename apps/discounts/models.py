from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator,MaxValueValidator
from decimal import Decimal
from django.utils import timezone
from apps.accounts.models import User
from apps.products.models import Product, Category

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES=[('percentage',_('Percentage')),('fixed',_('Fixed Amount')),('free_shipping',_('Free Shipping'))]
    code=models.CharField(_('code'),max_length=50,unique=True)
    description=models.TextField(_('description'),blank=True)
    discount_type=models.CharField(_('discount type'),max_length=20,choices=DISCOUNT_TYPE_CHOICES)
    discount_value=models.DecimalField(_('discount value'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    minimum_purchase=models.DecimalField(_('minimum purchase'),max_digits=10,decimal_places=2,null=True,blank=True,validators=[MinValueValidator(Decimal('0.00'))])
    maximum_discount=models.DecimalField(_('maximum discount'),max_digits=10,decimal_places=2,null=True,blank=True,validators=[MinValueValidator(Decimal('0.00'))])
    usage_limit=models.IntegerField(_('usage limit'),null=True,blank=True,validators=[MinValueValidator(1)])
    usage_limit_per_user=models.IntegerField(_('usage limit per user'),null=True,blank=True,validators=[MinValueValidator(1)])
    usage_count=models.IntegerField(_('usage count'),default=0)
    valid_from=models.DateTimeField(_('valid from'))
    valid_until=models.DateTimeField(_('valid until'))
    applicable_products=models.ManyToManyField(Product,blank=True,related_name='coupons',verbose_name=_('applicable products'))
    applicable_categories=models.ManyToManyField(Category,blank=True,related_name='coupons',verbose_name=_('applicable categories'))
    applicable_users=models.ManyToManyField(User,blank=True,related_name='exclusive_coupons',verbose_name=_('applicable users'))
    is_active=models.BooleanField(_('active'),default=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)

    class Meta:
        verbose_name=_('coupon'); verbose_name_plural=_('coupons'); ordering=['-created_at']

    def __str__(self): return self.code

    def is_valid(self):
        now=timezone.now()
        if not self.is_active: return False,'Not active'
        if now<self.valid_from: return False,'Not yet valid'
        if now>self.valid_until: return False,'Expired'
        if self.usage_limit and self.usage_count>=self.usage_limit: return False,'Usage limit reached'
        return True,'Valid'

    def can_user_use(self,user):
        valid,msg=self.is_valid()
        if not valid: return False,msg
        if self.applicable_users.exists() and user not in self.applicable_users.all(): return False,'Not for your account'
        if self.usage_limit_per_user:
            from .models import CouponUsage
            count=CouponUsage.objects.filter(coupon=self,user=user).count()
            if count>=self.usage_limit_per_user: return False,'Per-user limit reached'
        return True,'Can use'

    def calculate_discount(self,order_total,products=None):
        if self.minimum_purchase and order_total<self.minimum_purchase: return Decimal('0.00')
        if self.discount_type=='percentage':
            amount=order_total*self.discount_value/100
            if self.maximum_discount: amount=min(amount,self.maximum_discount)
        elif self.discount_type=='fixed':
            amount=min(self.discount_value,order_total)
        else:
            amount=Decimal('0.00')
        return amount

class CouponUsage(models.Model):
    coupon=models.ForeignKey(Coupon,on_delete=models.CASCADE,related_name='usages',verbose_name=_('coupon'))
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='coupon_usages',verbose_name=_('user'))
    order=models.ForeignKey('orders.Order',on_delete=models.CASCADE,related_name='coupon_usages',verbose_name=_('order'))
    discount_amount=models.DecimalField(_('discount amount'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)

    class Meta:
        verbose_name=_('coupon usage'); verbose_name_plural=_('coupon usages'); ordering=['-created_at']

    def __str__(self): return f"{self.coupon.code} – {self.user.email}"

class Sale(models.Model):
    name=models.CharField(_('name'),max_length=100)
    description=models.TextField(_('description'),blank=True)
    discount_percentage=models.DecimalField(_('discount percentage'),max_digits=5,decimal_places=2,validators=[MinValueValidator(Decimal('0.00')),MaxValueValidator(Decimal('100.00'))])
    applicable_products=models.ManyToManyField(Product,blank=True,related_name='sales',verbose_name=_('applicable products'))
    applicable_categories=models.ManyToManyField(Category,blank=True,related_name='sales',verbose_name=_('applicable categories'))
    valid_from=models.DateTimeField(_('valid from'))
    valid_until=models.DateTimeField(_('valid until'))
    is_active=models.BooleanField(_('active'),default=True)
    priority=models.IntegerField(_('priority'),default=0)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)

    class Meta:
        verbose_name=_('sale'); verbose_name_plural=_('sales'); ordering=['-priority','-created_at']

    def __str__(self): return self.name

    def is_valid(self): 
        now=timezone.now()
        return self.is_active and self.valid_from<=now<=self.valid_until
