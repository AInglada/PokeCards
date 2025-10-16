from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email: raise ValueError(_('El email debe ser proporcionado'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password); user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True: raise ValueError(_('Superuser debe tener is_staff=True'))
        if extra_fields.get('is_superuser') is not True: raise ValueError(_('Superuser debe tener is_superuser=True'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    is_subscribed_newsletter = models.BooleanField(_('newsletter subscription'), default=False)
    profile_image = models.ImageField(_('profile image'), upload_to='profiles/', null=True, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name']

    class Meta:
        verbose_name = _('user'); verbose_name_plural = _('users'); ordering = ['-created_at']

    def __str__(self): return self.email

class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [('shipping',_('Shipping')),('billing',_('Billing')),('both',_('Both'))]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name=_('user'))
    address_type = models.CharField(_('address type'), max_length=10, choices=ADDRESS_TYPE_CHOICES, default='both')
    full_name = models.CharField(_('full name'), max_length=100)
    phone_number = models.CharField(_('phone number'), max_length=20)
    address_line_1 = models.CharField(_('address line 1'), max_length=255)
    address_line_2 = models.CharField(_('address line 2'), max_length=255, blank=True)
    city = models.CharField(_('city'), max_length=100)
    state_province = models.CharField(_('state/province'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20)
    country = models.CharField(_('country'), max_length=100)
    is_default = models.BooleanField(_('default address'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('address'); verbose_name_plural = _('addresses'); ordering = ['-is_default','-created_at']

    def __str__(self): return f"{self.full_name} – {self.city}, {self.country}"

    def save(self,*args,**kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user,address_type=self.address_type,is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args,**kwargs)
