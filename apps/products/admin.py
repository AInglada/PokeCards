from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import Category, ProductType, Product, ProductImage, Inventory, Tag, ProductTag

@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ['name','parent','is_active','order']
    list_filter = ['is_active']
    search_fields = ['translations__name']
    # prepopulated_fields = {'slug':('name',)}

@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ['get_name_display']

class ProductImageInline(admin.TabularInline):
    model = ProductImage; extra=1

class InventoryInline(admin.StackedInline):
    model = Inventory; can_delete=False

@admin.register(Product)
class ProductAdmin(TranslatableAdmin):
    list_display = ['name','sku','category','selling_price','profit_margin','is_active','is_featured']
    list_filter = ['is_active','is_featured','category','product_type']
    search_fields = ['translations__name','sku']
    # prepopulated_fields = {'slug':('name',)}
    readonly_fields = ['profit_margin','profit_amount','is_on_sale','discount_percentage','created_at','updated_at']
    inlines = [ProductImageInline,InventoryInline]

@admin.register(Tag)
class TagAdmin(TranslatableAdmin):
    list_display = ['name']
    # prepopulated_fields = {'slug':('name',)}

@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ['product','tag']
