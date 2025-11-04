from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('bookings/', views.CreateBookingView.as_view(), name='create-booking'),
    path('payments/create/', views.CreatePaymentView.as_view(), name='create-payment'),
    path('payments/verify/', views.VerifyPaymentView.as_view(), name='verify-payment'),
]
