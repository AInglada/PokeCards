from django.contrib import admin
from .models import Coupon, CouponUsage, Sale

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code','discount_type','discount_value','usage_count','is_active','valid_until']
    list_filter = ['discount_type','is_active','valid_from','valid_until']
    search_fields = ['code']

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon','user','order','discount_amount','created_at']
    readonly_fields = ['created_at']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['name','discount_percentage','is_active','valid_from','valid_until']
    list_filter = ['is_active','valid_from','valid_until']
