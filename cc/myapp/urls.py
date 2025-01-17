from django.urls import path
from .views import du, adds 

urlpatterns = [
    path('du/', du, name='du'),
    path('adds/', adds, name='adds'),
]