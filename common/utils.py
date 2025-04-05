import uuid
import os
from datetime import timedelta
from django.utils import timezone


def get_file_path(instance, filename):
    """
    Generate a UUID-based file path for uploaded files.
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join(f'uploads/{instance.__class__.__name__.lower()}', filename)


def generate_random_code(length=6):
    """
    Generate a random verification code.
    """
    import random
    import string
    return ''.join(random.choices(string.digits, k=length))


def get_future_date(days=0, hours=0, minutes=0):
    """
    Returns a datetime object with the specified days, hours, and minutes added.
    """
    return timezone.now() + timedelta(days=days, hours=hours, minutes=minutes)


def is_valid_phone_number(phone_number):
    """
    Checks if a phone number is valid
    """
    import re
    # This is a simple pattern for illustration
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone_number))


def calculate_age(birth_date):
    """
    Calculate age from birth date
    """
    today = timezone.now().date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def anonymize_data(text):
    """
    Anonymize sensitive data in text
    """
    import re
    # Replace email addresses
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL]', text)
    # Replace phone numbers
    text = re.sub(r'\+?1?\d{9,15}', '[PHONE]', text)
    # Replace credit card numbers
    text = re.sub(r'\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}', '[CREDIT CARD]', text)
    return text