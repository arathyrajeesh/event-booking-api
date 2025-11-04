from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
import os

def qr_upload_path(instance, filename):
    return os.path.join('qr_codes', f"{instance.ticket_number}.png")

class User(AbstractUser):
    # username, email, password inherited
    name = models.CharField(max_length=120, blank=True)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username or self.email

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    available_tickets = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')

    def __str__(self):
        return f"{self.title} at {self.venue} on {self.date}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    num_tickets = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    booking_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Booking #{self.id} by {self.user}"

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    payment_id = models.CharField(max_length=255)  # PayPal order ID / capture ID
    payment_status = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.payment_id} ({self.payment_status})"

class Ticket(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='tickets')
    qr_code = models.ImageField(upload_to=qr_upload_path, blank=True, null=True)
    ticket_number = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    issued_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Ticket {self.ticket_number} for booking {self.booking.id}"
