"""Personal Assistant package for managing contacts and notes."""

from .address_book import AddressBook
from .cli import PersonalAssistantCLI, main
from .commands import AppContext
from .notes import Note, Notebook
from .record import ContactRecord
from .storage import Storage

__all__ = [
    "AddressBook",
    "AppContext",
    "ContactRecord",
    "Note",
    "Notebook",
    "PersonalAssistantCLI",
    "Storage",
    "main",
]


