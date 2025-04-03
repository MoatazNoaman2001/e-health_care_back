import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone_number(value):
    """
    Validate that the input is a valid phone number.
    """
    if not re.match(r'^\+?1?\d{9,15}$', value):
        raise ValidationError(
            _('Enter a valid phone number.'),
            code='invalid_phone_number',
        )


def validate_zip_code(value):
    """
    Validate that the input is a valid US zip code.
    """
    if not re.match(r'^\d{5}(-\d{4})?$', value):
        raise ValidationError(
            _('Enter a valid zip code.'),
            code='invalid_zip_code',
        )


def validate_password_strength(value):
    """
    Validate that the password has a minimum length and contains at least
    one uppercase letter, one lowercase letter, one digit, and one special character.
    """
    if len(value) < 8:
        raise ValidationError(
            _('Password must be at least 8 characters long.'),
            code='password_too_short',
        )

    if not re.search(r'[A-Z]', value):
        raise ValidationError(
            _('Password must contain at least one uppercase letter.'),
            code='password_no_uppercase',
        )

    if not re.search(r'[a-z]', value):
        raise ValidationError(
            _('Password must contain at least one lowercase letter.'),
            code='password_no_lowercase',
        )

    if not re.search(r'\d', value):
        raise ValidationError(
            _('Password must contain at least one digit.'),
            code='password_no_digit',
        )

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError(
            _('Password must contain at least one special character.'),
            code='password_no_special',
        )


def validate_future_date(value):
    """
    Validate that the date is in the future.
    """
    from django.utils import timezone

    if value < timezone.now().date():
        raise ValidationError(
            _('Date must be in the future.'),
            code='date_not_future',
        )


def validate_file_size(value):
    """
    Validate that the file size is under 5MB.
    """
    file_size = value.size
    limit_mb = 5
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(
            _('File size cannot exceed %s MB.') % limit_mb,
            code='file_too_large',
        )


def validate_image_dimensions(value):
    """
    Validate that the image dimensions are within reasonable limits.
    """
    from PIL import Image

    max_width = 2000
    max_height = 2000

    # Open the image
    img = Image.open(value)
    width, height = img.size

    if width > max_width or height > max_height:
        raise ValidationError(
            _('Image dimensions cannot exceed %s x %s pixels.') % (max_width, max_height),
            code='image_too_large',
        )