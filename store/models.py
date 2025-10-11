from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from django.contrib.auth.models import AbstractUser


# ---------------------
# USER & ADDRESSES
# ---------------------
class User(AbstractUser):
    full_name = models.CharField(max_length=120, blank=True, null=True)
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    tel_num = models.CharField(max_length=20, blank=True, null=True)

    # Use email as the authentication field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # keep username required for compatibility with admin

    def __str__(self):
        return f"{self.username} ({self.email})"


class UserAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=200)
    number = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    default = models.BooleanField(default=False)  # mark default shipping address
    address_type = models.CharField(max_length=20, default='shipping')  # e.g. 'shipping' or 'billing'

    def __str__(self):
        return f"{self.street} {self.number}, {self.city}"


# ---------------------
# GENERATIONS & SETS
# ---------------------
class Generation(models.Model):
    name = models.CharField(max_length=100)
    release_year = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class CardSet(models.Model):
    # renamed for clarity (avoid Python builtin name 'Set')
    generation = models.ForeignKey(Generation, on_delete=models.CASCADE, related_name='sets')
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    release_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


# ---------------------
# LANGUAGES & CONDITIONS
# ---------------------
class Language(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class CardCondition(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# ---------------------
# CARDS & INVENTORY
# ---------------------
# store/models.py  (replace the Card model with the following)

class Card(models.Model):
    """
    Represents a canonical card entry in the catalogue.

    We store both simple scalar fields (name, rarity, hp, image_url_small/large)
    and some JSON fields for complex structures (attacks, abilities, weaknesses).
    """
    set = models.ForeignKey(CardSet, on_delete=models.CASCADE, related_name='cards')
    # identifier within the set (e.g. "25" or "45/192")
    set_number = models.CharField(max_length=50, db_index=True)
    # optional id from pokemontcg.io (e.g. "swsh4-25")
    global_id = models.CharField(max_length=200, blank=True, null=True, unique=True)
    name = models.CharField(max_length=200)
    supertype = models.CharField(max_length=50, blank=True, null=True)   # e.g. "Pokémon", "Trainer"
    subtypes = models.CharField(max_length=200, blank=True, null=True)   # comma-separated or keep small
    hp = models.CharField(max_length=10, blank=True, null=True)
    types = models.CharField(max_length=200, blank=True, null=True)      # comma-separated types
    evolves_from = models.CharField(max_length=200, blank=True, null=True)
    rarity = models.CharField(max_length=50, blank=True, null=True)
    card_type = models.CharField(max_length=50, blank=True, null=True)   # legacy field (keep if used)
    # Textual fields
    artist = models.CharField(max_length=200, blank=True, null=True)
    flavor_text = models.TextField(blank=True, null=True)
    # Images
    image_url_small = models.URLField(blank=True, null=True)
    image_url_large = models.URLField(blank=True, null=True)
    # Market / external ids
    market_url_tcgplayer = models.URLField(blank=True, null=True)  
    market_url_cardmarket = models.URLField(blank=True, null=True)
    # Booleans
    is_holo = models.BooleanField(default=False)
    # Structured fields stored as JSON for flexibility
    national_pokedex_numbers = models.JSONField(blank=True, null=True)  # list of ints
    attacks = models.JSONField(blank=True, null=True)   # list of attack dicts
    abilities = models.JSONField(blank=True, null=True) # list of ability dicts
    weaknesses = models.JSONField(blank=True, null=True) # list of weakness dicts
    retreat_cost = models.JSONField(blank=True, null=True) # list or dict
    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('set', 'set_number')
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['set_number']),
            models.Index(fields=['global_id']),
        ]

    def __str__(self):
        return f"{self.name} ({self.set.code} #{self.set_number})"



class Inventory(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='inventory_items')
    condition = models.ForeignKey(CardCondition, on_delete=models.SET_NULL, null=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchased_at = models.DateField(default=timezone.now)
    market_price_latest = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        # optional: prevent duplicate inventory rows for same (card, condition, language)
        unique_together = ('card', 'condition', 'language')
        indexes = [
            models.Index(fields=['card']),
            models.Index(fields=['language']),
        ]

    @property
    def final_price(self):
        # Business rule: if no market price, markup 25% over purchase_price.
        # else choose max between markup and 95% of market price.
        try:
            if not self.market_price_latest:
                return (self.purchase_price * Decimal('1.25')).quantize(Decimal('.01'))
            candidate = max(self.purchase_price * Decimal('1.25'),
                            self.market_price_latest * Decimal('0.95'))
            return candidate.quantize(Decimal('.01'))
        except Exception:
            # fail-safe
            return self.purchase_price

    def __str__(self):
        return f"{self.card.name} x{self.quantity} ({self.condition})"


# ---------------------
# ORDERS
# ---------------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    # snapshot fields: we store the address data duplicated at order time to freeze it
    shipping_name = models.CharField(max_length=200, blank=True, null=True)
    shipping_street = models.CharField(max_length=200, blank=True, null=True)
    shipping_number = models.CharField(max_length=20, blank=True, null=True)
    shipping_city = models.CharField(max_length=100, blank=True, null=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True, null=True)
    shipping_country = models.CharField(max_length=100, blank=True, null=True)

    address = models.ForeignKey(UserAddress, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return f"Order #{self.id} by {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey(Inventory, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    # store the unit price at the time of purchase (freeze price)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    @property
    def total_price(self):
        if self.unit_price is not None:
            return self.unit_price * self.quantity
        return self.inventory_item.final_price * self.quantity

    def __str__(self):
        return f"{self.inventory_item.card.name} x{self.quantity}"
