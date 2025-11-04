from django.urls import path
from .views import (
    RegisterView, EventListView, EventDetailView, CreateBookingView,
    PayPalCreateOrder, PayPalCaptureOrder, MyBookingsView,
    AdminCreateEventView, AdminUpdateEventView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('events/', EventListView.as_view(), name='events_list'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event_detail'),

    path('bookings/', CreateBookingView.as_view(), name='create_booking'),
    path('bookings/my/', MyBookingsView.as_view(), name='my_bookings'),

    path('payments/create-order/', PayPalCreateOrder.as_view(), name='paypal_create_order'),
    path('payments/capture/', PayPalCaptureOrder.as_view(), name='paypal_capture_order'),

    # admin
    path('admin/events/', AdminCreateEventView.as_view(), name='admin_create_event'),
    path('admin/events/<int:pk>/', AdminUpdateEventView.as_view(), name='admin_update_event'),
]
