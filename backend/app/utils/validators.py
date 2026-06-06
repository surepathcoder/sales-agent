"""Domain validators for Tanzanian business data."""

import re

NIDA_PATTERN = re.compile(r"^\d{20}$")
BRELA_PATTERN = re.compile(r"^\d{5,12}$")


def validate_nida(nida: str) -> bool:
    """NIDA numbers are 20 digits."""
    return bool(NIDA_PATTERN.match(nida.replace(" ", "")))


def validate_brela_reg(reg_number: str) -> bool:
    """BRELA registration number format."""
    return bool(BRELA_PATTERN.match(reg_number.strip()))


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
    return slug.strip("-")[:100]
