from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .fields import Address, Birthday, Email, Name, Phone, ValidationError


class ContactRecord:
    """Represents a single contact with multiple fields."""

    def __init__(
        self,
        name: str,
        phones: Optional[Iterable[str]] = None,
        email: str | None = None,
        address: str | None = None,
        birthday: str | datetime | None = None,
    ) -> None:
        self.name = Name(name)
        self.phones: List[Phone] = []
        self.email: Email | None = Email(email) if email else None
        self.address: Address | None = Address(address) if address else None
        self.birthday: Birthday | None = Birthday(birthday) if birthday else None
        if phones:
            for phone in phones:
                self.add_phone(phone)

    def add_phone(self, phone: str) -> None:
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> bool:
        for idx, stored in enumerate(self.phones):
            if stored.value == phone:
                del self.phones[idx]
                return True
        return False

    def edit_phone(self, old: str, new: str) -> bool:
        for idx, stored in enumerate(self.phones):
            if stored.value == old:
                self.phones[idx] = Phone(new)
                return True
        return False

    def set_email(self, email: str | None) -> None:
        self.email = Email(email) if email else None

    def set_address(self, address: str | None) -> None:
        self.address = Address(address) if address else None

    def set_birthday(self, birthday: str | datetime | None) -> None:
        self.birthday = Birthday(birthday) if birthday else None

    def days_to_birthday(self, today: datetime | None = None) -> Optional[int]:
        if not self.birthday:
            return None
        if today is None:
            today = datetime.today()
        birthday_date = self.birthday.value.replace(year=today.year)
        if birthday_date < today:
            birthday_date = birthday_date.replace(year=today.year + 1)
        return (birthday_date - today).days

    def matches(self, query: str) -> bool:
        haystack = [
            self.name.value.lower(),
            *(phone.value for phone in self.phones),
        ]
        if self.email:
            haystack.append(self.email.value.lower())
        if self.address:
            haystack.append(self.address.value.lower())
        query_lower = query.lower()
        return any(query_lower in value.lower() for value in haystack)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name.value,
            "phones": [phone.value for phone in self.phones],
            "email": self.email.value if self.email else None,
            "address": self.address.value if self.address else None,
            "birthday": self.birthday.__str__() if self.birthday else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContactRecord":
        return cls(
            name=data["name"],
            phones=data.get("phones") or [],
            email=data.get("email"),
            address=data.get("address"),
            birthday=data.get("birthday"),
        )

    def __str__(self) -> str:
        phones = ", ".join(str(phone) for phone in self.phones) if self.phones else "-"
        email = str(self.email) if self.email else "-"
        address = str(self.address) if self.address else "-"
        birthday = str(self.birthday) if self.birthday else "-"
        return (
            f"{self.name.value} | Phones: {phones} | Email: {email} | "
            f"Address: {address} | Birthday: {birthday}"
        )


