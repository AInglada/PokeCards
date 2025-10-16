from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator,MaxValueValidator
from apps.accounts.models import User
from apps.products.models import Product

class Review(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='reviews',verbose_name=_('product'))
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='reviews',verbose_name=_('user'))
    rating=models.IntegerField(_('rating'),validators=[MinValueValidator(1),MaxValueValidator(5)])
    title=models.CharField(_('title'),max_length=200)
    comment=models.TextField(_('comment'))
    is_verified_purchase=models.BooleanField(_('verified purchase'),default=False)
    is_approved=models.BooleanField(_('approved'),default=True)
    helpful_count=models.IntegerField(_('helpful count'),default=0)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)
    updated_at=models.DateTimeField(_('updated at'),auto_now=True)

    class Meta:
        verbose_name=_('review'); verbose_name_plural=_('reviews'); ordering=['-created_at']; unique_together=('product','user')

    def __str__(self): return f"{self.user.email} – {self.product} ({self.rating}/5)"

class ReviewImage(models.Model):
    review=models.ForeignKey(Review,on_delete=models.CASCADE,related_name='images',verbose_name=_('review'))
    image=models.ImageField(_('image'),upload_to='reviews/')
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)

    class Meta:
        verbose_name=_('review image'); verbose_name_plural=_('review images')

    def __str__(self): return f"Image for review {self.review.id}"

class ReviewVote(models.Model):
    review=models.ForeignKey(Review,on_delete=models.CASCADE,related_name='votes',verbose_name=_('review'))
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='review_votes',verbose_name=_('user'))
    is_helpful=models.BooleanField(_('is helpful'),default=True)
    created_at=models.DateTimeField(_('created at'),auto_now_add=True)

    class Meta:
        verbose_name=_('review vote'); verbose_name_plural=_('review votes'); unique_together=('review','user')

    def __str__(self): return f"{self.user.email} – Review {self.review.id}"
