import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
from datetime import timezone
from zoneinfo import ZoneInfo

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL")

IST = ZoneInfo("Asia/Kolkata")


# ---------------------------------------------------------
# TIME FORMATTERS
# ---------------------------------------------------------

def format_datetime(dt, tz: ZoneInfo):
    """Convert UTC datetime to given timezone and format nicely"""
    local_dt = dt.astimezone(tz)

    date_str = local_dt.strftime("%d %B %Y")
    time_str = local_dt.strftime("%I:%M %p")
    return date_str, time_str


# ---------------------------------------------------------
# USER EMAIL TEMPLATE (User Timezone)
# ---------------------------------------------------------

def generate_user_email_template(booking):

    user_tz = ZoneInfo(
        booking.timezone if booking.timezone else "UTC"
    )

    date_str, time_str = format_datetime(
        booking.booking_datetime,
        user_tz
    )

    return f"""
    <!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>OneTracker Demo Confirmation</title>
</head>

<body style="margin:0; padding:0; background-color:#f4f6f9; font-family:Segoe UI, Arial, sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f6f9; padding:30px 0;">
<tr>
<td align="center">

<!-- Main Container -->
<table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff; border-collapse:collapse;">

    <!-- Header -->
    <tr>
        <td style="background-color:#F4B400; padding:30px 40px; color:#ffffff;">
            <span style="font-size:24px; font-weight:700; letter-spacing:0.5px;">
                OneTracker Technologies Pvt. Ltd.
            </span>
        </td>
    </tr>

    <!-- Body Content -->
    <tr>
        <td style="padding:40px; color:#1f2937; font-size:14px; line-height:1.6;">

            <p style="margin:0 0 16px 0;">
                Dear <strong>{booking.name}</strong>,
            </p>

            <p style="margin:0 0 16px 0;">
                Thank you for scheduling a product demonstration with <strong>OneTracker</strong>.
                We look forward to discussing how our tracking solutions can support 
                <strong>{booking.business_name}</strong>.
            </p>

            <!-- Meeting Details Box -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" 
                   style="margin:25px 0; background-color:#f9fafb; border:1px solid #e5e7eb;">
                <tr>
                    <td style="padding:20px; border-left:4px solid #229EBC ;">
                        
                        <p style="margin:0 0 12px 0; font-size:13px; font-weight:600; color:#F4B400; text-transform:uppercase;">
                            Meeting Details
                        </p>

                        <p style="margin:0 0 8px 0;">
                            <strong>Date:</strong> {date_str}
                        </p>

                        <p style="margin:0 0 8px 0;">
                            <strong>Time:</strong> {time_str} ({booking.timezone})
                        </p>

                        <p style="margin:0;">
                            <strong>Platform:</strong> Video Conference
                        </p>

                    </td>
                </tr>
            </table>

           

            

            <p style="margin:25px 0 0 0;">
                Regards,<br>
                <strong>The OneTracker Team</strong><br>
               <br>
                <img src="https://onetraker.com/wp-content/uploads/2025/09/ot_logo_1_1_small.png" alt="OneTracker_logo">
                <br>
                 OneTracker Technologies Pvt. Ltd.
               
            </p>

        </td>
    </tr>

    <!-- Footer -->
    <tr>
        <td style="background-color:#f9fafb; padding:25px 40px; font-size:12px; color:#6b7280; border-top:1px solid #e5e7eb;">
            This is an automated confirmation email.<br><br>
            © 2026 OneTracker Technologies Pvt. Ltd. All rights reserved.
        </td>
    </tr>

</table>
<!-- End Container -->

</td>
</tr>
</table>

</body>
</html>
    """


# ---------------------------------------------------------
# COMPANY EMAIL TEMPLATE (Always IST)
# ---------------------------------------------------------

def generate_company_email_template(booking):

    date_str, time_str = format_datetime(
        booking.booking_datetime,
        IST
    )

    return f"""
    <!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>New Demo Booking Received</title>
</head>

<body style="margin:0; padding:0; background-color:#f4f6f9; font-family:Segoe UI, Arial, sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f6f9; padding:30px 0;">
<tr>
<td align="center">

<!-- Main Container -->
<table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff; border-collapse:collapse;">

    <!-- Header -->
    <tr>
        <td style="background-color:#F4B400; padding:30px 40px; color:#e5e7eb;">
            <span style="font-size:22px; font-weight:700;">
                New Demo Booking Received
            </span>
        </td>
    </tr>

    <!-- Content -->
    <tr>
        <td style="padding:40px; color:#1f2937; font-size:14px; line-height:1.6;">

            <p style="margin:0 0 20px 0;">
                A new demo booking has been submitted via the OneTracker website.
                The details are provided below for your review and follow-up.
            </p>

            <!-- Booking Details Box -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" 
                   style="margin:20px 0; background-color:#f9fafb; border:1px solid #e5e7eb;">
                <tr>
                    <td style="padding:20px; border-left:4px solid #229EBC;">

                        <p style="margin:0 0 12px 0; font-size:13px; font-weight:600; color:#F4B400; text-transform:uppercase;">
                            Booking Information
                        </p>

                        <p style="margin:0 0 8px 0;">
                            <strong>Name:</strong> {booking.name}
                        </p>

                        <p style="margin:0 0 8px 0;">
                            <strong>Business:</strong> {booking.business_name}
                        </p>

                        <p style="margin:0 0 8px 0;">
                            <strong>Work Email:</strong> {booking.work_email}
                        </p>

                        <p style="margin:0 0 8px 0;">
                            <strong>Contact Number:</strong> {booking.contact_number}
                        </p>

                        <p style="margin:0 0 8px 0;">
                            <strong>Date (IST):</strong> {date_str}
                        </p>

                        <p style="margin:0 0 8px 0;">
                            <strong>Time (IST):</strong> {time_str}
                        </p>

                        <p style="margin:0 0 8px 0;">
                            <strong>User Timezone:</strong> {booking.timezone}
                        </p>

                        <p style="margin:0;">
                            <strong>Message:</strong><br>
                            {booking.message}
                        </p>

                    </td>
                </tr>
            </table>

            <p style="margin:20px 0 0 0;">
                Please ensure timely follow-up and schedule confirmation.
            </p><br>
             <img src="https://onetraker.com/wp-content/uploads/2025/09/ot_logo_1_1_small.png" alt="OneTracker_logo">

        </td>
    </tr>

    <!-- Footer -->
    <tr>
        <td style="background-color:#f9fafb; padding:25px 40px; font-size:12px; color:#6b7280; border-top:1px solid #e5e7eb;">
            This is an automated internal notification generated by the OneTracker booking system.<br><br>
            © 2026 OneTracker Technologies Pvt. Ltd. All rights reserved.
        </td>
    </tr>

</table>
<!-- End Container -->

</td>
</tr>
</table>

</body>
</html>
    """


# ---------------------------------------------------------
# SEND EMAIL FUNCTION
# ---------------------------------------------------------

def send_booking_email(booking):
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)

            # -----------------------
            # Email to User
            # -----------------------
            user_msg = EmailMessage()
            user_msg["Subject"] = "OneTracker Demo Booking Confirmation"
            user_msg["From"] = SMTP_USER
            user_msg["To"] = booking.work_email

            user_msg.set_content("Your email client does not support HTML.")
            user_msg.add_alternative(
                generate_user_email_template(booking),
                subtype="html"
            )

            server.send_message(user_msg)

            # -----------------------
            # Email to Sales Team (IST)
            # -----------------------
            company_msg = EmailMessage()
            company_msg["Subject"] = "New Demo Booking Received"
            company_msg["From"] = SMTP_USER
            company_msg["To"] = COMPANY_EMAIL

            company_msg.set_content("New demo booking received.")
            company_msg.add_alternative(
                generate_company_email_template(booking),
                subtype="html"
            )

            server.send_message(company_msg)

    except Exception as e:
        print("Email sending failed:", str(e))
