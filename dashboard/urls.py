from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='dashboard'),
    path('inventory/', inventory, name='inventory'),
    path('purchases/', purchases, name='purchases'),
    path('sales/', sales, name='sales'),
    path('expenses/', expenses, name='expenses'),
]