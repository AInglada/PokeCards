from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.core.validators import MinValueValidator
from apps.accounts.models import User, Address
from apps.products.models import Product

class Cart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='carts',verbose_name=_('user'))
    session_key=models.CharField(_('session key'),max_length=40,null=True,blank=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)
    class Meta:
        verbose_name=_('cart'); verbose_name_plural=_('carts')
    def __str__(self): return f"Cart for {self.user.email}" if self.user else f"Anonymous {self.session_key}"
    @property
    def total_items(self): return sum(item.quantity for item in self.items.all())
    @property
    def subtotal(self): return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='items',verbose_name=_('cart'))
    product=models.ForeignKey(Product,on_delete=models.CASCADE,verbose_name=_('product'))
    quantity=models.IntegerField(_('quantity'),default=1,validators=[MinValueValidator(1)])
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)
    class Meta:
        verbose_name=_('cart item'); verbose_name_plural=_('cart items'); unique_together=('cart','product')
    def __str__(self): return f"{self.quantity}x {self.product}"
    @property
    def total_price(self): return self.product.selling_price*self.quantity

class Order(models.Model):
    STATUS_CHOICES=[('pending',_('Pending')),('processing',_('Processing')),('shipped',_('Shipped')),('delivered',_('Delivered')),('cancelled',_('Cancelled')),('refunded',_('Refunded'))]
    PAYMENT_STATUS_CHOICES=[('pending',_('Pending')),('completed',_('Completed')),('failed',_('Failed')),('refunded',_('Refunded'))]
    order_number=models.CharField(_('order number'),max_length=50,unique=True)
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='orders',verbose_name=_('user'))
    email=models.EmailField(_('email'))
    phone_number=models.CharField(_('phone number'),max_length=20)
    shipping_address=models.ForeignKey(Address,on_delete=models.SET_NULL,null=True,related_name='shipping_orders',verbose_name=_('shipping address'))
    billing_address=models.ForeignKey(Address,on_delete=models.SET_NULL,null=True,related_name='billing_orders',verbose_name=_('billing address'))
    status=models.CharField(_('status'),max_length=20,choices=STATUS_CHOICES,default='pending')
    payment_status=models.CharField(_('payment status'),max_length=20,choices=PAYMENT_STATUS_CHOICES,default='pending')
    subtotal=models.DecimalField(_('subtotal'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    shipping_cost=models.DecimalField(_('shipping cost'),max_digits=10,decimal_places=2,default=Decimal('0.00'),validators=[MinValueValidator(Decimal('0.00'))])
    tax=models.DecimalField(_('tax'),max_digits=10,decimal_places=2,default=Decimal('0.00'),validators=[MinValueValidator(Decimal('0.00'))])
    discount_amount=models.DecimalField(_('discount amount'),max_digits=10,decimal_places=2,default=Decimal('0.00'),validators=[MinValueValidator(Decimal('0.00'))])
    total=models.DecimalField(_('total'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    customer_notes=models.TextField(_('customer notes'),blank=True)
    admin_notes=models.TextField(_('admin notes'),blank=True)
    tracking_number=models.CharField(_('tracking number'),max_length=100,blank=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)
    paid_at=models.DateTimeField(_('paid at'),null=True,blank=True)
    shipped_at=models.DateTimeField(_('shipped at'),null=True,blank=True)
    delivered_at=models.DateTimeField(_('delivered at'),null=True,blank=True)

    class Meta:
        verbose_name=_('order'); verbose_name_plural=_('orders'); ordering=['-created_at']

    def __str__(self): return f"Order #{self.order_number}"
    @property
    def total_profit(self): return sum(item.profit for item in self.items.all())

class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items',verbose_name=_('order'))
    product=models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,verbose_name=_('product'))
    product_name=models.CharField(_('product name'),max_length=255)
    product_sku=models.CharField(_('product SKU'),max_length=100)
    cost_price=models.DecimalField(_('cost price'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    selling_price=models.DecimalField(_('selling price'),max_digits=10,decimal_places=2,validators=[MinValueValidator(Decimal('0.00'))])
    quantity=models.IntegerField(_('quantity'),validators=[MinValueValidator(1)])
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)

    class Meta:
        verbose_name=_('order item'); verbose_name_plural=_('order items')

    def __str__(self): return f"{self.quantity}x {self.product_name}"
    @property
    def total_price(self): return self.selling_price*self.quantity
    @property
    def profit(self): return (self.selling_price-self.cost_price)*self.quantity

class OrderStatusHistory(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='status_history',verbose_name=_('order'))
    status=models.CharField(_('status'),max_length=20)
    notes=models.TextField(_('notes'),blank=True)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,verbose_name=_('created by'))
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)

    class Meta:
        verbose_name=_('order status history'); verbose_name_plural=_('order status histories'); ordering=['-created_at']

    def __str__(self): return f"{self.order.order_number} – {self.status}"

class Wishlist(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='wishlists',verbose_name=_('user'))
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='wishlisted_by',verbose_name=_('product'))
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)

    class Meta:
        verbose_name=_('wishlist'); verbose_name_plural=_('wishlists'); unique_together=('user','product'); ordering=['-created_at']

    def __str__(self): return f"{self.user.email} – {self.product}"
