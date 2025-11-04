from rest_framework import generics, status, permissions
from rest_framework.response import Response
from .models import Event, Booking, Payment, Ticket
from .serializers import EventSerializer, BookingSerializer, PaymentSerializer, TicketSerializer
import razorpay
from django.conf import settings
from django.utils.crypto import get_random_string

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# ----------------------------
#  Event List / Detail
# ----------------------------
class EventListView(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]


class EventDetailView(generics.RetrieveAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]


# ----------------------------
#  Booking API
# ----------------------------
class CreateBookingView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        event = serializer.validated_data['event']
        num_tickets = serializer.validated_data['num_tickets']
        total = event.ticket_price * num_tickets
        serializer.save(user=self.request.user, total_amount=total)


# ----------------------------
#  Razorpay Payment API
# ----------------------------
class CreatePaymentView(generics.CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        booking_id = request.data.get('booking_id')
        booking = Booking.objects.get(id=booking_id, user=request.user)
        amount = int(booking.total_amount * 100)  # in paise

        order = razorpay_client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": "1"
        })

        return Response({"order_id": order['id'], "amount": booking.total_amount})


class VerifyPaymentView(generics.CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        booking = Booking.objects.get(id=data.get('booking_id'))

        payment = Payment.objects.create(
            booking=booking,
            payment_id=data.get('payment_id'),
            payment_status='Success',
            amount=booking.total_amount
        )

        booking.status = 'Confirmed'
        booking.save()

        # Generate ticket
        ticket = Ticket.objects.create(
            booking=booking,
            ticket_number=get_random_string(10).upper()
        )

        return Response({
            "message": "Payment verified and ticket generated.",
            "ticket_id": ticket.id
        }, status=status.HTTP_200_OK)
