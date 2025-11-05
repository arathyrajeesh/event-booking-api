import qrcode
from io import BytesIO
from django.core.mail import EmailMessage
from django.conf import settings

def generate_qr_image(ticket_number):
    img = qrcode.make(ticket_number)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def attach_qr_and_send_email(user_email, subject, body, ticket_obj):
    """
    Sends email with QR code attached.
    Handles file reading safely and logs errors instead of crashing.
    """
    try:
        email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [user_email])

        if ticket_obj.qr_code and ticket_obj.qr_code.name:
            # Open file safely
            ticket_obj.qr_code.open(mode='rb')
            email.attach(f"{ticket_obj.ticket_number}.png", ticket_obj.qr_code.read(), 'image/png')
            ticket_obj.qr_code.close()

        # Send email safely
        email.send(fail_silently=False)

    except Exception as e:
        print(f"Email sending failed: {e}")
        # Don't crash the payment flow
