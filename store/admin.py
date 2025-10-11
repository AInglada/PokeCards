from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _

from .models import (
    User, UserAddress, Generation, CardSet, Language, CardCondition,
    Card, Inventory, Order, OrderItem
)

# ---------- Custom user forms ----------
class UserCreationForm(forms.ModelForm):
    """
    A form for creating new users. Includes all required fields + repeated password.
    """
    password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'), widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'username', 'full_name')

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """
    Form for updating users. Replace password field with read-only hash display.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'is_active', 'is_staff', 'is_superuser')


# ---------- UserAdmin ----------
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ('email', 'username', 'full_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('full_name', 'gender', 'tel_num')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'username', 'full_name')
    ordering = ('email',)


# ---------- Register other models ----------
@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'street', 'number', 'city', 'postal_code', 'country', 'default')
    list_filter = ('country', 'default')
    search_fields = ('user__email', 'street', 'city')

@admin.register(Generation)
class GenerationAdmin(admin.ModelAdmin):
    list_display = ('name', 'release_year')

@admin.register(CardSet)
class CardSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'generation', 'release_date')
    search_fields = ('name', 'code')

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(CardCondition)
class CardConditionAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('name', 'set', 'set_number', 'global_id', 'rarity', 'is_holo', 'market_url_tcgplayer', 'market_url_cardmarket')
    search_fields = ('name', 'set_number', 'global_id', 'artist', 'market_url_tcgplayer', 'market_url_cardmarket')
    list_filter = ('set', 'rarity', 'is_holo')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('global_id', 'name', 'set', 'set_number', 'supertype', 'subtypes', 'hp', 'types', 'evolves_from', 'rarity', 'card_type', 'is_holo')
        }),
        ('Text & Media', {
            'fields': ('artist', 'flavor_text', 'image_url_small', 'image_url_large')
        }),
        ('Market URLs', {
            'fields': ('market_url_tcgplayer', 'market_url_cardmarket')
        }),
        ('Structured data (JSON)', {
            'fields': ('national_pokedex_numbers', 'abilities', 'attacks', 'weaknesses', 'retreat_cost')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('card', 'condition', 'language', 'quantity', 'purchase_price', 'market_price_latest')
    list_filter = ('condition', 'language')
    search_fields = ('card__name', 'card__set_number')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('unit_price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]
