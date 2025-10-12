from django.shortcuts import render
from django.http import HttpResponse
from .models import Card, CardSet, Generation, Language, CardCondition, Inventory
from random import sample
#from apps.banners.models import Banner

def home_view(request):
    """
    Simple home view for the catalog app
    """
    # Get banners
    ## banners = Banner.objects.filter(active=True)[:5]
    
    # Get random cards
    all_cards = list(Card.objects.all()[:100])
    random_cards = sample(all_cards, k=min(8, len(all_cards)))
    
    context = {
        ##'banners': banners,
        'random_cards': random_cards,
        'default_image_url': '/static/catalog/img/placeholders/no-image.png',
    }
    return render(request, 'catalog/home.html', context)

# You can add more views here as needed
# def card_list(request):
#     cards = Card.objects.all()
#     return render(request, 'catalog/card_list.html', {'cards': cards})

