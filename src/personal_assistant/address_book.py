from __future__ import annotations

from collections import UserDict
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from .record import ContactRecord


class AddressBook(UserDict[str, ContactRecord]):
    """Container for contact records with helper search utilities."""

    def add_record(self, record: ContactRecord) -> None:
        self.data[record.name.value.lower()] = record

    def get(self, name: str) -> Optional[ContactRecord]:
        return self.data.get(name.lower())

    def remove(self, name: str) -> bool:
        return self.data.pop(name.lower(), None) is not None

    def search(self, query: str) -> List[ContactRecord]:
        query_lower = query.lower()
        return [
            record
            for record in self.data.values()
            if record.matches(query_lower)
        ]

    def upcoming_birthdays(
        self, days_ahead: int, today: datetime | None = None
    ) -> List[ContactRecord]:
        today = today or datetime.today()
        matches: List[ContactRecord] = []
        for record in self.data.values():
            days_to_birthday = record.days_to_birthday(today=today)
            if days_to_birthday is not None and 0 <= days_to_birthday <= days_ahead:
                matches.append(record)
        return matches

    def to_list(self) -> List[ContactRecord]:
        return list(self.data.values())

    def to_serializable(self) -> List[Dict[str, str]]:
        return [record.to_dict() for record in self.data.values()]

    @classmethod
    def from_serializable(cls, data: Iterable[Dict[str, str]]) -> "AddressBook":
        book = cls()
        for entry in data:
            book.add_record(ContactRecord.from_dict(entry))
        return book


