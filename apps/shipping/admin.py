from django.contrib import admin
from .models import ShippingZone, ShippingMethod, ShippingRate

@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ['name','is_active']
    list_filter = ['is_active']

@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ['name','zone','base_cost','is_active']
    list_filter = ['is_active','zone']

@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['order','shipping_method','cost','weight_kg']
    readonly_fields = ['tracking_number','tracking_url']
