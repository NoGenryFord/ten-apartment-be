import os
from pathlib import Path

from django.conf import settings
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from apartments.models import Booking, BookingSlot, Inquiry


SENDGRID_ENV_PATH = Path(__file__).resolve().parents[2] / "endgrid.env"
if SENDGRID_ENV_PATH.exists():
    load_dotenv(SENDGRID_ENV_PATH)


def send_booking_confirmation_email(booking: Booking) -> int:
    if not booking.email:
        raise ValueError("Booking email is missing.")

    api_key = getattr(settings, "SENDGRID_API_KEY", None) or os.getenv(
        "SENDGRID_API_KEY"
    )
    from_email = getattr(settings, "SENDGRID_FROM_EMAIL", None) or os.getenv(
        "SENDGRID_FROM_EMAIL"
    )

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
    guest_name = (
        booking.user.first_name if booking.user and booking.user.first_name else "guest"
    )

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
        ),
        plain_text_content=(
            f"Hello, {guest_name}!\n\n"
            f"Your booking has been confirmed.\n"
            f"Apartment: {apartment.name}\n"
            f"Check-in: {check_in}\n"
            f"Check-out: {check_out}\n"
            f"Total price: {booking.total_price} CZK\n"
        ),
    )

    client = SendGridAPIClient(api_key)
    response = client.send(message)
    return response.status_code


def send_inquiry_notification_email(inquiry: Inquiry) -> int:
    """Send a notification to the owner when a contact form inquiry is submitted."""
    api_key = getattr(settings, "SENDGRID_API_KEY", None) or os.getenv(
        "SENDGRID_API_KEY"
    )
    from_email = getattr(settings, "SENDGRID_FROM_EMAIL", None) or os.getenv(
        "SENDGRID_FROM_EMAIL"
    )
    owner_email = getattr(settings, "OWNER_EMAIL", None) or os.getenv("OWNER_EMAIL")

    if not api_key:
        raise ValueError("SENDGRID_API_KEY is not configured.")
    if not from_email:
        raise ValueError("SENDGRID_FROM_EMAIL is not configured.")
    if not owner_email:
        raise ValueError("OWNER_EMAIL is not configured.")

    apartment_line = (
        f"<br /><strong>Apartment:</strong> {inquiry.apartment}"
        if inquiry.apartment
        else ""
    )

    message = Mail(
        from_email=from_email,
        to_emails=owner_email,
        subject=f"New inquiry from {inquiry.name}",
        html_content=(
            f"<p>You received a new inquiry from the website.</p>"
            f"<p>"
            f"<strong>Name:</strong> {inquiry.name}<br />"
            f"<strong>Contact:</strong> {inquiry.contact}"
            f"{apartment_line}"
            f"</p>"
            f"<p><strong>Message:</strong><br />{inquiry.message}</p>"
        ),
        plain_text_content=(
            f"New inquiry from {inquiry.name}\n\n"
            f"Contact: {inquiry.contact}\n"
            + (f"Apartment: {inquiry.apartment}\n" if inquiry.apartment else "")
            + f"\nMessage:\n{inquiry.message}\n"
        ),
    )

    client = SendGridAPIClient(api_key)
    response = client.send(message)
    return response.status_code
