# apps/pagesapp/views.py
from django.shortcuts import render, get_object_or_404
from .models import Article


def news_list_view(request):
    """Display list of published news articles"""
    articles = Article.objects.filter(published=True).order_by('-published_at')
    return render(request, 'pagesapp/news_list.html', {'articles': articles})


def news_detail_view(request, slug):
    """Display single news article detail"""
    article = get_object_or_404(Article, slug=slug, published=True)
    return render(request, 'pagesapp/news_detail.html', {'article': article})

