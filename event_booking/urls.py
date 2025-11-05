"""
URL configuration for event_booking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# event_booking/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Dummy views for PayPal redirects
def payment_success(request):
    return HttpResponse("Payment completed! You can close this page.")

def payment_cancel(request):
    return HttpResponse("Payment cancelled.")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('events.urls')),  # your existing API URLs
    path('api/payments/success/', payment_success),  # PayPal success redirect
    path('api/payments/cancel/', payment_cancel),    # PayPal cancel redirect
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
