import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(to: str, subject: str, body: str):
    """
    Send a simple email using Zoho SMTP.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content
    """
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = "support@saasgrowthdispatch.com"
        msg["To"] = to

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.zoho.com", 465) as server:
            server.login(
                "support@saasgrowthdispatch.com", os.getenv("ZOHO_APP_PASSWORD")
            )
            server.sendmail(msg["From"], msg["To"], msg.as_string())
            print(f"✅ Email sent to {to}")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
