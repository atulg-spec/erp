from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .models import CustomUser
import json

class UpdateUserLocationView(View):
    @method_decorator(login_required)  # Ensures that the user is logged in
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user = request.user  # Get the logged-in user

            # Update the user model with the new location data
            user.region_name = data.get('region_name', user.region_name)
            user.city = data.get('city', user.city)
            user.zip_code = data.get('zip_code', user.zip_code)
            user.lat = data.get('lat', user.lat)
            user.lon = data.get('lon', user.lon)
            user.timezone = data.get('timezone', user.timezone)
            user.isp = data.get('isp', user.isp)

            user.save()  # Save the changes to the user model

            return JsonResponse({"message": "User data updated successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
