"""services/email_service.py - SMTP email + OTP generation"""

import os
import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from utils.db import get_db

OTP_EXPIRY_MINUTES = 10


def generate_otp(length=6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def get_email_delivery_mode() -> str:
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    return 'email' if smtp_user and smtp_pass else 'console'


def save_otp(email: str, otp: str):
    db = get_db()
    db.otps.update_one(
        {'email': email},
        {'$set': {
            'otp': otp,
            'expires_at': datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
            'used': False
        }},
        upsert=True
    )


def verify_otp(email: str, otp: str) -> bool:
    db = get_db()
    record = db.otps.find_one({'email': email, 'used': False})
    if not record:
        return False
    if record['otp'] != otp:
        return False
    if datetime.utcnow() > record['expires_at']:
        return False
    db.otps.update_one({'email': email}, {'$set': {'used': True}})
    return True


def send_otp_email(email: str, otp: str, name: str = 'User') -> bool:
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')

    if not smtp_user or not smtp_pass:
        # Dev mode: just print OTP
        print(f"\n[EMAIL DEV MODE] OTP for {email}: {otp}\n")
        return True

    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; background: #f8fafc; padding: 40px 20px;">
      <div style="background: white; border-radius: 16px; padding: 40px; box-shadow: 0 4px 24px rgba(0,0,0,0.06);">
        <div style="text-align: center; margin-bottom: 32px;">
          <div style="background: linear-gradient(135deg, #0ea5e9, #06b6d4); display: inline-block; padding: 12px 24px; border-radius: 12px;">
            <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 700;">Alpha-Cure</h1>
          </div>
        </div>
        <h2 style="color: #1e293b; margin-bottom: 8px;">Hello, {name}!</h2>
        <p style="color: #64748b; font-size: 15px; line-height: 1.6;">
          Your email verification OTP for Alpha-Cure is:
        </p>
        <div style="text-align: center; margin: 32px 0;">
          <div style="background: #f0f9ff; border: 2px dashed #0ea5e9; border-radius: 12px; padding: 24px; display: inline-block;">
            <span style="font-size: 40px; font-weight: 800; letter-spacing: 12px; color: #0284c7;">{otp}</span>
          </div>
        </div>
        <p style="color: #94a3b8; font-size: 13px; text-align: center;">
          This OTP expires in {OTP_EXPIRY_MINUTES} minutes. Do not share this with anyone.
        </p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
        <p style="color: #cbd5e1; font-size: 12px; text-align: center;">
          Alpha-Cure — AI-Powered Cancer Detection & Care Platform
        </p>
      </div>
    </div>
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Alpha-Cure: Your OTP is {otp}'
        msg['From'] = f'Alpha-Cure <{smtp_user}>'
        msg['To'] = email
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [email], msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False
