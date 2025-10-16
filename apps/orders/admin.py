from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory, Wishlist

class CartItemInline(admin.TabularInline):
    model = CartItem; extra=0; readonly_fields=['total_price']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id','user','total_items','subtotal','updated_at']
    search_fields = ['user__email','session_key']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user','product','created_at']
    search_fields = ['user__email','product__translations__name']

class OrderItemInline(admin.TabularInline):
    model = OrderItem; extra=0; readonly_fields=['total_price','profit']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number','user','status','total','total_profit','created_at']
    list_filter = ['status','payment_status','created_at']
    search_fields = ['order_number','email']
    readonly_fields = ['order_number','subtotal','total','total_profit','created_at','updated_at','paid_at','shipped_at','delivered_at']
    inlines = [OrderItemInline]

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order','status','created_by','created_at']
    readonly_fields = ['created_at']
