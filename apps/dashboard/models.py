from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from apps.accounts.models import User
from apps.products.models import Product
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment

class Dashboard:
    """
    Dashboard analytics service - no database model needed.
    Static methods for analytics calculations.
    """
    
    @staticmethod
    def get_sales_summary(start_date=None, end_date=None):
        """Get sales summary for date range."""
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date],
            status__in=['processing', 'shipped', 'delivered']
        )
        
        return {
            'total_orders': orders.count(),
            'total_revenue': orders.aggregate(Sum('total'))['total__sum'] or 0,
            'total_profit': sum(order.total_profit for order in orders),
            'average_order_value': orders.aggregate(Avg('total'))['total__avg'] or 0,
        }
    
    @staticmethod
    def get_product_performance():
        """Get top performing products."""
        from django.db.models import F
        
        top_products = OrderItem.objects.values(
            'product__id',
            'product__translations__name',
            'product__sku'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('selling_price') * F('quantity')),
            total_profit=Sum((F('selling_price') - F('cost_price')) * F('quantity'))
        ).order_by('-total_revenue')[:10]
        
        return list(top_products)
    
    @staticmethod
    def get_low_stock_products():
        """Get products with low stock."""
        from apps.products.models import Inventory
        
        low_stock = Inventory.objects.filter(
            quantity__lte=F('low_stock_threshold')
        ).select_related('product')
        
        return [{
            'product_id': inv.product.id,
            'product_name': inv.product.name,
            'sku': inv.product.sku,
            'current_stock': inv.quantity,
            'threshold': inv.low_stock_threshold,
            'is_out_of_stock': inv.is_out_of_stock
        } for inv in low_stock]
    
    @staticmethod
    def get_recent_orders(limit=10):
        """Get recent orders."""
        orders = Order.objects.select_related('user').order_by('-created_at')[:limit]
        
        return [{
            'order_number': order.order_number,
            'customer': order.user.get_full_name() if order.user else order.email,
            'total': order.total,
            'status': order.status,
            'created_at': order.created_at,
            'profit': order.total_profit
        } for order in orders]
    
    @staticmethod
    def get_customer_stats():
        """Get customer statistics."""
        total_customers = User.objects.filter(is_staff=False).count()
        new_customers_month = User.objects.filter(
            is_staff=False,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        returning_customers = User.objects.filter(
            is_staff=False,
            orders__isnull=False
        ).annotate(
            order_count=Count('orders')
        ).filter(order_count__gt=1).count()
        
        return {
            'total_customers': total_customers,
            'new_customers_month': new_customers_month,
            'returning_customers': returning_customers,
            'customer_retention_rate': (returning_customers / total_customers * 100) if total_customers > 0 else 0
        }
    
    @staticmethod
    def get_monthly_sales_chart(months=12):
        """Get monthly sales data for chart."""
        from django.db.models.functions import TruncMonth
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months * 30)
        
        monthly_data = Order.objects.filter(
            created_at__range=[start_date, end_date],
            status__in=['processing', 'shipped', 'delivered']
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('total'),
            profit=Sum('total') - Sum('subtotal')  # Simplified calculation
        ).order_by('month')
        
        return list(monthly_data)
    
    @staticmethod
    def get_top_categories():
        """Get top selling categories."""
        from django.db.models import F
        from apps.products.models import Category
        
        category_sales = OrderItem.objects.select_related(
            'product__category'
        ).values(
            'product__category__id',
            'product__category__translations__name'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('selling_price') * F('quantity'))
        ).order_by('-total_revenue')[:5]
        
        return list(category_sales)


class SystemAlert(models.Model):
    """System alerts for dashboard notifications."""
    
    ALERT_TYPE_CHOICES = [
        ('low_stock', _('Low Stock')),
        ('payment_failed', _('Payment Failed')),
        ('high_refund_rate', _('High Refund Rate')),
        ('system_error', _('System Error')),
        ('security', _('Security Alert')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]
    
    alert_type = models.CharField(
        _('alert type'), 
        max_length=20, 
        choices=ALERT_TYPE_CHOICES
    )
    priority = models.CharField(
        _('priority'), 
        max_length=10, 
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))
    
    # Related objects (optional)
    related_product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('related product')
    )
    related_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('related order')
    )
    related_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('related user')
    )
    
    # Status
    is_read = models.BooleanField(_('is read'), default=False)
    is_resolved = models.BooleanField(_('is resolved'), default=False)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        verbose_name=_('resolved by')
    )
    resolved_at = models.DateTimeField(_('resolved at'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('system alert')
        verbose_name_plural = _('system alerts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['is_read']),
            models.Index(fields=['is_resolved']),
        ]

    def __str__(self):
        return f'{self.get_priority_display()} - {self.title}'

    def mark_as_read(self):
        """Mark alert as read."""
        self.is_read = True
        self.save()

    def resolve(self, resolved_by=None):
        """Mark alert as resolved."""
        self.is_resolved = True
        self.resolved_by = resolved_by
        self.resolved_at = timezone.now()
        self.save()

    @classmethod
    def create_low_stock_alert(cls, product):
        """Create low stock alert for product."""
        return cls.objects.create(
            alert_type='low_stock',
            priority='medium',
            title=f'Low Stock: {product.name}',
            message=f'Product {product.sku} has low stock ({product.inventory.available_quantity} remaining).',
            related_product=product
        )

    @classmethod
    def create_payment_failed_alert(cls, payment):
        """Create payment failed alert."""
        return cls.objects.create(
            alert_type='payment_failed',
            priority='high',
            title=f'Payment Failed: {payment.transaction_id}',
            message=f'Payment for order {payment.order.order_number} failed.',
            related_order=payment.order,
            related_user=payment.user
        )


class DashboardWidget(models.Model):
    """Dashboard widget configuration for admin users."""
    
    WIDGET_TYPE_CHOICES = [
        ('sales_summary', _('Sales Summary')),
        ('recent_orders', _('Recent Orders')),
        ('low_stock', _('Low Stock Products')),
        ('top_products', _('Top Products')),
        ('customer_stats', _('Customer Statistics')),
        ('alerts', _('System Alerts')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_widgets',
        verbose_name=_('user')
    )
    widget_type = models.CharField(
        _('widget type'), 
        max_length=20, 
        choices=WIDGET_TYPE_CHOICES
    )
    position = models.IntegerField(_('position'), default=0)
    is_visible = models.BooleanField(_('visible'), default=True)
    size = models.CharField(
        _('size'), 
        max_length=10, 
        choices=[('small', _('Small')), ('medium', _('Medium')), ('large', _('Large'))],
        default='medium'
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('dashboard widget')
        verbose_name_plural = _('dashboard widgets')
        ordering = ['user', 'position']
        unique_together = ('user', 'widget_type')

    def __str__(self):
        return f'{self.user.email} - {self.get_widget_type_display()}'
