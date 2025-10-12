# apps/pagesapp/urls.py
from django.urls import path
from . import views

app_name = 'pagesapp'

urlpatterns = [
    path('news/', views.news_list_view, name='news_list'),
    path('news/<slug:slug>/', views.news_detail_view, name='news_detail'),
]
