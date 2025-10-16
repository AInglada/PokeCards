from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

class ShippingZone(models.Model):
    name=models.CharField(_('name'),max_length=100)
    countries=models.JSONField(_('countries'),default=list,help_text=_('List of country codes'))
    is_active=models.BooleanField(_('active'),default=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)

    class Meta:
        verbose_name=_('shipping zone'); verbose_name_plural=_('shipping zones'); ordering=['name']

    def __str__(self): return self.name

class ShippingMethod(models.Model):
    name=models.CharField(_('name'),max_length=100)
    description=models.TextField(_('description'),blank=True)
    zone=models.ForeignKey(ShippingZone,on_delete=models.CASCADE,related_name='shipping_methods',verbose_name=_('shipping zone'))
    base_cost=models.DecimalField(_('base cost'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    cost_per_kg=models.DecimalField(_('cost per kg'),max_digits=10,decimal_places=2,default=Decimal('0.00'),validators=[MinValueValidator(Decimal('0.00'))])
    free_shipping_threshold=models.DecimalField(_('free shipping threshold'),max_digits=10,decimal_places=2,null=True,blank=True,validators=[MinValueValidator(Decimal('0.00'))])
    estimated_days_min=models.IntegerField(_('estimated minimum days'),default=1,validators=[MinValueValidator(1)])
    estimated_days_max=models.IntegerField(_('estimated maximum days'),default=7,validators=[MinValueValidator(1)])
    provider=models.CharField(_('provider'),max_length=50,blank=True)
    provider_service_code=models.CharField(_('provider service code'),max_length=50,blank=True)
    is_active=models.BooleanField(_('active'),default=True)
    order=models.IntegerField(_('order'),default=0)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)

    class Meta:
        verbose_name=_('shipping method'); verbose_name_plural=_('shipping methods'); ordering=['zone','order','name']

    def __str__(self): return f"{self.name} – {self.zone}"

    def calculate_cost(self, order_total, weight_kg=0):
        if self.free_shipping_threshold and order_total>=self.free_shipping_threshold:
            return Decimal('0.00')
        return self.base_cost + (self.cost_per_kg*Decimal(str(weight_kg)))

class ShippingRate(models.Model):
    order=models.OneToOneField('orders.Order',on_delete=models.CASCADE,related_name='shipping_rate',verbose_name=_('order'))
    shipping_method=models.ForeignKey(ShippingMethod,on_delete=models.SET_NULL,null=True,verbose_name=_('shipping method'))
    cost=models.DecimalField(_('cost'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    weight_kg=models.DecimalField(_('weight (kg)'),max_digits=10,decimal_places=3,default=Decimal('0.000'),validators=[MinValueValidator(Decimal('0.000'))])
    tracking_number=models.CharField(_('tracking number'),max_length=100,blank=True)
    tracking_url=models.URLField(_('tracking URL'),blank=True)
    carrier=models.CharField(_('carrier'),max_length=100,blank=True)
    service_name=models.CharField(_('service name'),max_length=100,blank=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)

    class Meta:
        verbose_name=_('shipping rate'); verbose_name_plural=_('shipping rates')

    def __str__(self): return f"Shipping for Order #{self.order.order_number}"
