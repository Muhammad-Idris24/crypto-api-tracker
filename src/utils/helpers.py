import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def send_email_alert(subject: str, body: str):
    """Send an email alert using SMTP."""
    sender = os.getenv("ALERT_EMAIL")
    password = os.getenv("ALERT_PASSWORD")
    recipient = os.getenv("ALERT_RECIPIENT") or sender
    
    if not all([sender, password]):
        print("Email alert configuration incomplete. Skipping email notification.")
        return
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("Email alert sent successfully!")
    except Exception as e:
        print(f"Failed to send email alert: {str(e)}")