from django.shortcuts import render
from django.http import JsonResponse
from .utils import ask_gemini

def assistant_chat(request):
    if request.method == "POST":
        user_message = request.POST.get("message")
        bot_response = ask_gemini(user_message)
        return JsonResponse({"response": bot_response})
    
    return render(request, "assistant/chat.html")