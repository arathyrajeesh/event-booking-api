from rest_framework import serializers
from .models import User, Event, Booking, Payment, Ticket
from django.contrib.auth.password_validation import validate_password
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'name')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ('created_by',)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('payment_date',)


class TicketSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ['ticket_number', 'qr_code_url', 'issued_at']

    def get_qr_code_url(self, obj):
        request = self.context.get('request')
        if obj.qr_code and request:
            return request.build_absolute_uri(obj.qr_code.url)
        return None

class BookingSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'event', 'event_title', 'user', 'user_email',
            'num_tickets', 'total_amount', 'status', 'booking_date', 'tickets'
        ]
        read_only_fields = ('user', 'total_amount', 'status', 'booking_date')
