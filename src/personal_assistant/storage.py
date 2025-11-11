from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from .address_book import AddressBook
from .notes import Notebook


DEFAULT_STORAGE_DIR = Path.home() / ".personal_assistant"
CONTACTS_FILE = "contacts.json"
NOTES_FILE = "notes.json"


class Storage:
    """Handles persistence of contacts and notes."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or DEFAULT_STORAGE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.contacts_path = self.base_dir / CONTACTS_FILE
        self.notes_path = self.base_dir / NOTES_FILE

    def load(self) -> Tuple[AddressBook, Notebook]:
        address_book = AddressBook()
        notebook = Notebook()

        if self.contacts_path.exists():
            with self.contacts_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                address_book = AddressBook.from_serializable(data)

        if self.notes_path.exists():
            with self.notes_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                notebook = Notebook.from_serializable(data)

        return address_book, notebook

    def save(self, address_book: AddressBook, notebook: Notebook) -> None:
        with self.contacts_path.open("w", encoding="utf-8") as fh:
            json.dump(address_book.to_serializable(), fh, indent=2, ensure_ascii=False)
        with self.notes_path.open("w", encoding="utf-8") as fh:
            json.dump(notebook.to_serializable(), fh, indent=2, ensure_ascii=False)


