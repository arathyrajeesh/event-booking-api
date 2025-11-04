from django.contrib import admin
from .models import User, Event, Booking, Payment, Ticket

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_admin', 'is_staff', 'is_superuser')
    list_filter = ('is_admin', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'name')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'venue', 'date', 'time', 'ticket_price', 'available_tickets', 'created_by')
    list_filter = ('date', 'venue')
    search_fields = ('title', 'venue', 'description')
    ordering = ('-date',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'num_tickets', 'total_amount', 'status', 'booking_date')
    list_filter = ('status', 'booking_date')
    search_fields = ('user__username', 'event__title')
    ordering = ('-booking_date',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'payment_id', 'payment_status', 'amount', 'payment_date')
    list_filter = ('payment_status',)
    search_fields = ('payment_id', 'booking__user__username')
    ordering = ('-payment_date',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'ticket_number', 'issued_at')
    search_fields = ('ticket_number', 'booking__user__username')
    ordering = ('-issued_at',)
