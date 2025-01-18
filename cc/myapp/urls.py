from django.urls import path
from .views import du, adds, display_ads 

urlpatterns = [
    path('du/', du, name='du'),
    path('adds/', adds, name='adds'),
    path('display_ads/', display_ads, name='display_ads'), 
]