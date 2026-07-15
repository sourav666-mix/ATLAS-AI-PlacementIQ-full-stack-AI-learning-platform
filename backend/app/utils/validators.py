# validators.py - input sanitization
# backend/app/utils/validators.py
"""
Small reusable validation helpers (used by Pydantic schemas and services).

Kept dependency-free and pure so they're trivial to unit-test.
"""
import re

_PASSWORD_MIN_LEN = 8
# at least one letter and one digit; length checked separately for a clear message
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def normalize_email(email: str) -> str:
    """Trim + lowercase so 'A@B.com ' and 'a@b.com' are the same account."""
    return email.strip().lower()


def validate_password_strength(password: str) -> str:
    """
    Enforce a minimal policy. Returns the password unchanged if OK,
    otherwise raises ValueError with a human-readable reason.
    """
    if len(password) < _PASSWORD_MIN_LEN:
        raise ValueError(f"Password must be at least {_PASSWORD_MIN_LEN} characters.")
    if not _HAS_LETTER.search(password):
        raise ValueError("Password must contain at least one letter.")
    if not _HAS_DIGIT.search(password):
        raise ValueError("Password must contain at least one digit.")
    return password


__all__ = ["normalize_email", "validate_password_strength"]