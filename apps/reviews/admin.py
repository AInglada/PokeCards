from django.contrib import admin
from .models import Review, ReviewImage, ReviewVote

class ReviewImageInline(admin.TabularInline):
    model = ReviewImage; extra=1

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product','user','rating','is_verified_purchase','is_approved','helpful_count','created_at']
    list_filter = ['rating','is_verified_purchase','is_approved','created_at']
    search_fields = ['product__translations__name','user__email','title']
    readonly_fields = ['helpful_count','created_at','updated_at']
    inlines = [ReviewImageInline]

@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ['review','user','is_helpful','created_at']
    readonly_fields = ['created_at']
