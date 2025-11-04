from django.db import models
from django.contrib.auth.models import AbstractUser
import qrcode
from io import BytesIO
from django.core.files import File


#  Custom User Model

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username



#  Event Model

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    venue = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    ticket_price = models.DecimalField(max_digits=8, decimal_places=2)
    available_tickets = models.PositiveIntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')

    def __str__(self):
        return self.title



#  Booking Model

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    num_tickets = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    booking_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"



#  Payment Model

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.booking}"



#  Ticket Model (QR code)

class Ticket(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    ticket_number = models.CharField(max_length=20, unique=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ticket_number

    def save(self, *args, **kwargs):
        qr_content = f"Ticket: {self.ticket_number} | Event: {self.booking.event.title} | User: {self.booking.user.username}"
        qr_img = qrcode.make(qr_content)
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        self.qr_code.save(f"{self.ticket_number}.png", File(buffer), save=False)
        super().save(*args, **kwargs)
