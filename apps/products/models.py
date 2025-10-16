from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from django.core.validators import MinValueValidator
from decimal import Decimal

class Category(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=100),
        description=models.TextField(_('description'), blank=True),
    )
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children', verbose_name=_('parent category'))
    image = models.ImageField(_('image'), upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    order = models.IntegerField(_('order'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name=_('category'); verbose_name_plural=_('categories'); ordering=['order','id']

    def __str__(self): return self.safe_translation_getter('name', any_language=True)

class ProductType(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('single_card',_('Single Card')),('booster_pack',_('Booster Pack')),
        # ... demás opciones ...
        ('other_accessory',_('Other Accessory'))
    ]
    name = models.CharField(_('name'), max_length=50, choices=PRODUCT_TYPE_CHOICES, unique=True)

    class Meta:
        verbose_name=_('product type'); verbose_name_plural=_('product types')

    def __str__(self): return self.get_name_display()

class Product(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_('name'), max_length=255),
        description=models.TextField(_('description'), blank=True),
        short_description=models.CharField(_('short description'), max_length=500, blank=True),
    )
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    sku = models.CharField(_('SKU'), max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,
                                 related_name='products', verbose_name=_('category'))
    product_type = models.ForeignKey(ProductType, on_delete=models.SET_NULL, null=True,
                                     related_name='products', verbose_name=_('product type'))
    cost_price = models.DecimalField(_('cost price'), max_digits=10, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.00'))])
    selling_price = models.DecimalField(_('selling price'), max_digits=10, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.00'))])
    compare_at_price = models.DecimalField(_('compare at price'), max_digits=10, decimal_places=2,
                                           null=True, blank=True, validators=[MinValueValidator(Decimal('0.00'))])
    set_name = models.CharField(_('set/expansion name'), max_length=100, blank=True)
    card_number = models.CharField(_('card number'), max_length=20, blank=True)
    rarity = models.CharField(_('rarity'), max_length=50, blank=True)
    language = models.CharField(_('language'), max_length=20, default='English')
    condition = models.CharField(_('condition'), max_length=20, blank=True)
    main_image = models.ImageField(_('main image'), upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_featured = models.BooleanField(_('featured'), default=False)
    meta_title = models.CharField(_('meta title'), max_length=70, blank=True)
    meta_description = models.CharField(_('meta description'), max_length=160, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name=_('product'); verbose_name_plural=_('products'); ordering=['-created_at']
        indexes=[models.Index(fields=['slug']),models.Index(fields=['sku'])]

    def __str__(self): return self.safe_translation_getter('name', any_language=True)

    @property
    def profit_margin(self):
        return ((self.selling_price-self.cost_price)/self.selling_price*100) if self.selling_price>0 else 0

    @property
    def profit_amount(self):
        return self.selling_price-self.cost_price

    @property
    def is_on_sale(self):
        return self.compare_at_price and self.compare_at_price>self.selling_price

    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return ((self.compare_at_price-self.selling_price)/self.compare_at_price*100)
        return 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name=_('product'))
    image = models.ImageField(_('image'), upload_to='products/')
    alt_text = models.CharField(_('alt text'), max_length=255, blank=True)
    order = models.IntegerField(_('order'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name=_('product image'); verbose_name_plural=_('product images'); ordering=['order','created_at']

    def __str__(self): return f"{self.product} – Image {self.order}"

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory', verbose_name=_('product'))
    quantity = models.IntegerField(_('quantity'), default=0, validators=[MinValueValidator(0)])
    reserved_quantity = models.IntegerField(_('reserved quantity'), default=0, validators=[MinValueValidator(0)])
    low_stock_threshold = models.IntegerField(_('low stock threshold'), default=10, validators=[MinValueValidator(0)])
    warehouse_location = models.CharField(_('warehouse location'), max_length=100, blank=True)
    last_restocked = models.DateTimeField(_('last restocked'), null=True, blank=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name=_('inventory'); verbose_name_plural=_('inventories')

    @property
    def available_quantity(self):
        return max(0, self.quantity-self.reserved_quantity)

    @property
    def is_low_stock(self):
        return self.available_quantity<=self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.available_quantity<=0

    def reserve_stock(self,qty):
        if self.available_quantity>=qty:
            self.reserved_quantity+=qty; self.save(); return True
        return False

    def release_stock(self,qty):
        self.reserved_quantity=max(0,self.reserved_quantity-qty); self.save()

    def deduct_stock(self,qty):
        self.quantity=max(0,self.quantity-qty)
        self.reserved_quantity=max(0,self.reserved_quantity-qty)
        self.save()

class Tag(TranslatableModel):
    translations=TranslatedFields(name=models.CharField(_('name'),max_length=50))
    slug=models.SlugField(_('slug'),max_length=50,unique=True)
    class Meta:
        verbose_name=_('tag'); verbose_name_plural=_('tags')
    def __str__(self): return self.safe_translation_getter('name',any_language=True)

class ProductTag(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='product_tags')
    tag=models.ForeignKey(Tag,on_delete=models.CASCADE,related_name='product_tags')
    class Meta:
        unique_together=('product','tag'); verbose_name=_('product tag'); verbose_name_plural=_('product tags')
    def __str__(self): return f"{self.product} – {self.tag}"
