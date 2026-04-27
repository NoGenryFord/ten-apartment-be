import os
from pathlib import Path

from django.conf import settings
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from apartments.models import Booking, BookingSlot


SENDGRID_ENV_PATH = Path(__file__).resolve().parents[2] / "endgrid.env"
if SENDGRID_ENV_PATH.exists():
    load_dotenv(SENDGRID_ENV_PATH)


def send_booking_confirmation_email(booking: Booking) -> int:
    if not booking.email:
        raise ValueError("Booking email is missing.")

    api_key = getattr(settings, "SENDGRID_API_KEY", None) or os.getenv("SENDGRID_API_KEY")
    from_email = getattr(settings, "SENDGRID_FROM_EMAIL", None) or os.getenv("SENDGRID_FROM_EMAIL")

    if not api_key:
        raise ValueError("SENDGRID_API_KEY is not configured.")
    if not from_email:
        raise ValueError("SENDGRID_FROM_EMAIL is not configured.")

    slots = list(
        BookingSlot.objects.filter(booking=booking)
        .select_related("schedule__apartment")
        .order_by("schedule__date")
    )
    if not slots:
        raise ValueError("Booking has no booked slots.")

    apartment = slots[0].schedule.apartment
    check_in = slots[0].schedule.date.strftime("%d.%m.%Y")
    check_out = slots[-1].schedule.date.strftime("%d.%m.%Y")
    guest_name = booking.user.first_name if booking.user and booking.user.first_name else "guest"

    message = Mail(
        from_email=from_email,
        to_emails=booking.email,
        subject=f"Booking confirmed: {apartment.name}",
        html_content=(
            f"<strong>Hello, {guest_name}!</strong>"
            f"<p>Your booking has been confirmed.</p>"
            f"<p><strong>Apartment:</strong> {apartment.name}<br />"
            f"<strong>Check-in:</strong> {check_in}<br />"
            f"<strong>Check-out:</strong> {check_out}<br />"
            f"<strong>Total price:</strong> {booking.total_price} CZK<br />"
            f"<strong>Booking ID:</strong> {booking.id}</p>"
        ),
        plain_text_content=(
            f"Hello, {guest_name}!\n\n"
            f"Your booking has been confirmed.\n"
            f"Apartment: {apartment.name}\n"
            f"Check-in: {check_in}\n"
            f"Check-out: {check_out}\n"
            f"Total price: {booking.total_price} CZK\n"
            f"Booking ID: {booking.id}\n"
        ),
    )

    client = SendGridAPIClient(api_key)
    response = client.send(message)
    return response.status_code
