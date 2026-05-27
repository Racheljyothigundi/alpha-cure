"""Razorpay client helpers for consultation payments."""

import os
import razorpay

CONSULTATION_AMOUNT_INR = int(os.getenv('CONSULTATION_AMOUNT_INR', '5'))
CONSULTATION_AMOUNT_PAISE = CONSULTATION_AMOUNT_INR * 100


def get_razorpay_credentials():
    key_id = os.getenv('RAZORPAY_KEY_ID')
    key_secret = os.getenv('RAZORPAY_KEY_SECRET')
    placeholders = {'', 'your_razorpay_key_id_here', 'your_razorpay_key_secret_here'}
    if not key_id or key_id in placeholders or not key_secret or key_secret in placeholders:
        return None, None
    return key_id, key_secret


def get_razorpay_client():
    key_id, key_secret = get_razorpay_credentials()
    if not key_id:
        return None, None
    return razorpay.Client(auth=(key_id, key_secret)), key_id


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> None:
    client, _ = get_razorpay_client()
    if not client:
        raise ValueError('Razorpay is not configured')
    client.utility.verify_payment_signature({
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature,
    })
