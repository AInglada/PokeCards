from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import User, Address

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email','first_name','last_name','is_staff','is_subscribed_newsletter','created_at']
    list_filter = ['is_staff','is_superuser','is_subscribed_newsletter']
    search_fields = ['email','first_name','last_name']
    readonly_fields = ['created_at','updated_at']
    fieldsets = (
        (None,{'fields':('email','password')}),
        (_('Personal Info'),{'fields':('first_name','last_name','phone_number','date_of_birth','profile_image')}),
        (_('Permissions'),{'fields':('is_active','is_staff','is_superuser','groups','user_permissions')}),
        (_('Marketing'),{'fields':('is_subscribed_newsletter',)}),
        (_('Dates'),{'fields':('created_at','updated_at')}),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user','full_name','city','country','address_type','is_default']
    list_filter = ['address_type','country','is_default']
    search_fields = ['user__email','full_name','city']
    readonly_fields = ['created_at','updated_at']
