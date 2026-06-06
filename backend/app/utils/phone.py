"""Tanzanian phone number normalization (+255 format)."""

import re

TZ_PHONE_PATTERN = re.compile(r"^\+?255\d{9}$")


def normalize_tz_phone(phone: str) -> str:
    """
    Normalize to E.164 Tanzania format: +255XXXXXXXXX.

  Handles: 0712345678, 712345678, 255712345678, +255712345678
    """
    digits = re.sub(r"\D", "", phone)

    if digits.startswith("255") and len(digits) == 12:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 10:
        return f"+255{digits[1:]}"
    if len(digits) == 9:
        return f"+255{digits}"

    raise ValueError(f"Invalid Tanzanian phone number: {phone}")


def is_valid_tz_phone(phone: str) -> bool:
    try:
        normalized = normalize_tz_phone(phone)
        return bool(TZ_PHONE_PATTERN.match(normalized))
    except ValueError:
        return False
