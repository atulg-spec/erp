from django.urls import path
from .views import UpdateUserLocationView

urlpatterns = [
    path('update-user-location/', UpdateUserLocationView.as_view(), name='update_user_location'),
]
