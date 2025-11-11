from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional


class ValidationError(ValueError):
    """Raised when a field value fails validation."""


class Field:
    """Base descriptor for validated data fields."""

    def __init__(self, value: Any | None = None) -> None:
        self._value: Any | None = None
        if value is not None:
            self.value = value

    def validate(self, value: Any) -> Any:
        """Override in subclasses to validate the raw value."""
        return value

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        self._value = self.validate(value)

    def __str__(self) -> str:
        return str(self.value) if self.value is not None else ""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"


class Name(Field):
    def validate(self, value: str) -> str:
        if not value or not value.strip():
            raise ValidationError("Name cannot be empty.")
        return value.strip()


class Phone(Field):
    PHONE_PATTERN = re.compile(r"^\+?\d{7,15}$")

    def validate(self, value: str) -> str:
        digits = value.strip().replace(" ", "")
        if not self.PHONE_PATTERN.match(digits):
            raise ValidationError(
                "Phone number must contain 7-15 digits and may start with '+'."
            )
        return digits


class Email(Field):
    EMAIL_PATTERN = re.compile(
        r"^(?=.{3,254}$)(?!.*\.\.)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    def validate(self, value: str) -> str:
        cleaned = value.strip()
        if not self.EMAIL_PATTERN.match(cleaned):
            raise ValidationError("Invalid email format.")
        return cleaned


class Address(Field):
    def validate(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValidationError("Address cannot be empty.")
        return cleaned


class Birthday(Field):
    DATE_FORMAT = "%Y-%m-%d"

    def validate(self, value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            return value
        try:
            return datetime.strptime(value.strip(), self.DATE_FORMAT)
        except ValueError as exc:
            raise ValidationError(
                f"Birthday must be in {self.DATE_FORMAT} format."
            ) from exc

    def __str__(self) -> str:
        return self.value.strftime(self.DATE_FORMAT) if self.value else ""


