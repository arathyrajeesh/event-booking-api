from django.http import HttpResponse
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Event, Booking, Payment, Ticket, User
from .serializers import EventSerializer, BookingSerializer, PaymentSerializer, TicketSerializer, UserRegisterSerializer
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import transaction
import requests
from .utils import generate_qr_image, attach_qr_and_send_email
from django.core.files.base import ContentFile
import uuid
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone

# Register view
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

# Events
class EventListView(generics.ListAPIView):
    queryset = Event.objects.all().order_by('date')
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]


class EventDetailView(generics.RetrieveAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]

# Create booking (status PENDING)
class CreateBookingView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        event = serializer.validated_data['event']
        num = serializer.validated_data['num_tickets']

        if num > event.available_tickets:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Not enough tickets available.")

        total = num * event.ticket_price
        # reduce tickets temporarily or keep as-is until payment confirmed? We'll reserve by decrementing here:
        event.available_tickets -= num
        event.save()

        serializer.save(user=user, total_amount=total, status='PENDING')

# PayPal helper: get access token
def get_paypal_access_token():
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    r = requests.post(
        f"{settings.PAYPAL_BASE}/v1/oauth2/token",
        headers=headers,
        auth=auth,
        data={'grant_type': 'client_credentials'}
    )
    r.raise_for_status()
    return r.json()['access_token']

# Create PayPal order (returns orderID to client)
# Create PayPal order (returns orderID to client)
class PayPalCreateOrder(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        if booking.status != 'PENDING':
            return Response({"detail": "Booking not pending"}, status=status.HTTP_400_BAD_REQUEST)

        total = "{:.2f}".format(float(booking.total_amount))  # ensure string "10.00"
        token = get_paypal_access_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD" ,# or "INR" if supported
                        "value": total
                    },
                    "description": f"Booking #{booking.id} - {booking.event.title}"
                }
            ],
            "application_context": {
                "brand_name": "Event Booking API",
                "landing_page": "NO_PREFERENCE",
                "user_action": "PAY_NOW",
                "return_url": f"http://127.0.0.1:8000/api/payments/success/?booking_id={booking.id}",
                "cancel_url": "http://127.0.0.1:8000/api/payments/cancel/"
            }
        }

        # ✅ properly indented inside the method
        r = requests.post(f"{settings.PAYPAL_BASE}/v2/checkout/orders", json=payload, headers=headers)
        if r.status_code >= 400:
            print("PAYPAL ERROR:", r.text)  # for debugging
            return Response(
                {"detail": "PayPal order creation failed", "error": r.text},
                status=r.status_code
            )

        data = r.json()
        order_id = data.get("id")
        approval_link = next(
            (link["href"] for link in data.get("links", []) if link["rel"] == "approve"),
            None
        )

        return Response({
            "orderID": order_id,
            "approval_url": approval_link,
            "paypal_response": data
        }, status=status.HTTP_200_OK)


# Capture / Verify PayPal order server-side
class PayPalCaptureOrder(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        order_id = request.data.get('order_id')
        booking_id = request.data.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        token = get_paypal_access_token()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        # capture payment
        r = requests.post(f"{settings.PAYPAL_BASE}/v2/checkout/orders/{order_id}/capture", headers=headers)
        if r.status_code >= 400:
            return Response({"detail": "Failed to capture"}, status=status.HTTP_400_BAD_REQUEST)
        capture_data = r.json()

        # Mark payment record
        # extract capture id and status
        capture_id = None
        capture_status = None
        try:
            results = capture_data['purchase_units'][0]['payments']['captures'][0]
            capture_id = results['id']
            capture_status = results['status']
            amount = results['amount']['value']
        except Exception:
            # fallback
            capture_id = order_id
            capture_status = capture_data.get('status', 'COMPLETED')
            amount = booking.total_amount

        payment = Payment.objects.create(
            booking=booking,
            payment_id=capture_id,
            payment_status=capture_status,
            amount=amount
        )

        # Update booking status
        booking.status = 'CONFIRMED'
        booking.save()

        # Generate tickets (one Ticket per requested seat)
        tickets = []
        for i in range(booking.num_tickets):
            ticket_number = str(uuid.uuid4())
            ticket = Ticket.objects.create(booking=booking, ticket_number=ticket_number)
            # generate QR image, save to ticket.qr_code
            img_buffer = generate_qr_image(ticket_number)
            ticket.qr_code.save(f"{ticket_number}.png", ContentFile(img_buffer.getvalue()))
            ticket.save()
            tickets.append(ticket)
        # Send email to user with ticket(s) attached (here attaching only first ticket image for brevity)
        user_email = booking.user.email
        subject = f"Booking Confirmed - {booking.event.title}"
        body = f"Hello {booking.user.username},\n\nYour booking #{booking.id} is confirmed. Attached is your ticket QR code. Ticket count: {booking.num_tickets}\n\nRegards,\nEvent Team"

        # send email and attach QR(s)
        # We'll attach first ticket; you can loop to attach all
        if tickets:
            attach_qr_and_send_email(user_email, subject, body, tickets[0])

        return Response({"detail": "Payment captured and booking confirmed",
                        "payment_id": payment.payment_id,
                        "payment_status": payment.payment_status,
                        "tickets": [
                            {
                                "ticket_number": t.ticket_number,
                                "qr_code_url": request.build_absolute_uri(t.qr_code.url)
                            } for t in tickets
                        ]
                        }, status=status.HTTP_200_OK)


# View user's bookings
class MyBookingsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by('-booking_date')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  # Needed for full QR code URLs
        return context

# Admin Event management (simple examples)
class AdminCreateEventView(generics.CreateAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin only")
        serializer.save(created_by=user)

class AdminUpdateEventView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        user = self.request.user
        if not user.is_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Admin only")
        serializer.save()
        
def payment_success(request):
    booking_id = request.GET.get('booking_id')
    booking = Booking.objects.get(id=booking_id)
    tickets = Ticket.objects.filter(booking=booking)

    html = f"<h2>Booking Confirmed: #{booking.id}</h2>"
    for t in tickets:
        qr_url = request.build_absolute_uri(t.qr_code.url)
        html += f"<p>Ticket: {t.ticket_number}<br><img src='{qr_url}' width='200'/></p>"

    return HttpResponse(html)
