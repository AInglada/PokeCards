from django.contrib import admin
from .models import PaymentGateway, Payment, Refund

@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['display_name','name','is_active','is_test_mode','order']
    list_filter = ['is_active','is_test_mode']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id','order','gateway','amount','status','created_at']
    list_filter = ['status','gateway','created_at']
    search_fields = ['transaction_id','gateway_transaction_id']

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['refund_id','payment','amount','status','created_at']
    list_filter = ['status','reason','created_at']
