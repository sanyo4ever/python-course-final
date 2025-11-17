from __future__ import annotations

import shlex
from dataclasses import dataclass
from datetime import datetime
from difflib import get_close_matches
from typing import Callable, Dict, Iterable, List, Optional

from .address_book import AddressBook
from .fields import ValidationError
from .notes import Note, Notebook
from .record import ContactRecord
from .storage import Storage


@dataclass
class AppContext:
    address_book: AddressBook
    notebook: Notebook
    storage: Storage


@dataclass
class CommandResult:
    message: str
    should_exit: bool = False


CommandFunc = Callable[[AppContext, str], CommandResult]


class CommandError(Exception):
    """Domain-specific error for command processing."""


def parse_key_value_args(tokens: List[str]) -> Dict[str, str]:
    """Parse key=value pairs from a list of tokens.
    
    Args:
        tokens: List of already-split tokens (from shlex.split)
    
    Returns:
        Dictionary of key-value pairs with lowercase keys
    """
    pairs: Dict[str, str] = {}
    for token in tokens:
        if "=" not in token:
            continue
        key, value = token.split("=", maxsplit=1)
        pairs[key.strip().lower()] = value.strip()
    return pairs


def require_name(argument_string: str) -> str:
    if not argument_string.strip():
        raise CommandError("Name is required for this command.")
    return argument_string.strip()


def add_contact(context: AppContext, arguments: str) -> CommandResult:
    if not arguments:
        raise CommandError(
            "Usage: add contact <name> [phone=<number> ...] "
            "[email=<email>] [address=<address>] [birthday=YYYY-MM-DD]"
        )

    tokens = shlex.split(arguments)
    name = tokens[0]
    kv_args = parse_key_value_args(tokens[1:])

    record = ContactRecord(
        name=name,
        phones=[value for key, value in kv_args.items() if key.startswith("phone")],
        email=kv_args.get("email"),
        address=kv_args.get("address"),
        birthday=kv_args.get("birthday"),
    )
    context.address_book.add_record(record)
    context.storage.save(context.address_book, context.notebook)
    return CommandResult(f"Contact '{name}' added.")


def list_contacts(context: AppContext, _: str) -> CommandResult:
    contacts = context.address_book.to_list()
    if not contacts:
        return CommandResult("No contacts stored yet.")
    lines = ["Contacts:"]
    for record in contacts:
        lines.append(f"- {record}")
    return CommandResult("\n".join(lines))


def show_contact(context: AppContext, arguments: str) -> CommandResult:
    name = require_name(arguments)
    record = context.address_book.get(name)
    if not record:
        raise CommandError(f"Contact '{name}' not found.")
    return CommandResult(str(record))


def edit_contact(context: AppContext, arguments: str) -> CommandResult:
    tokens = shlex.split(arguments)
    if not tokens:
        raise CommandError(
            "Usage: edit contact <name> field=<value>. "
            "Supported fields: phone, email, address, birthday."
        )
    name = tokens[0]
    record = context.address_book.get(name)
    if not record:
        raise CommandError(f"Contact '{name}' not found.")

    updates = parse_key_value_args(tokens[1:])
    if not updates:
        raise CommandError("Provide fields to update, e.g. phone=+380..., email=foo@bar.")

    messages: List[str] = []
    try:
        for key, value in updates.items():
            if key.startswith("phone"):
                if ":" in value:
                    old, new = value.split(":", maxsplit=1)
                    if record.edit_phone(old, new):
                        messages.append(f"Updated phone {old} -> {new}.")
                    else:
                        messages.append(f"Phone {old} not found.")
                else:
                    record.add_phone(value)
                    messages.append(f"Added phone {value}.")
            elif key == "email":
                record.set_email(value or None)
                messages.append("Email updated.")
            elif key == "address":
                record.set_address(value or None)
                messages.append("Address updated.")
            elif key == "birthday":
                record.set_birthday(value or None)
                messages.append("Birthday updated.")
            else:
                messages.append(f"Ignored unsupported field '{key}'.")
    except ValidationError as error:
        raise CommandError(str(error)) from error

    context.storage.save(context.address_book, context.notebook)
    return CommandResult("\n".join(messages))


def delete_contact(context: AppContext, arguments: str) -> CommandResult:
    name = require_name(arguments)
    if context.address_book.remove(name):
        context.storage.save(context.address_book, context.notebook)
        return CommandResult(f"Contact '{name}' deleted.")
    raise CommandError(f"Contact '{name}' not found.")


def search_contacts(context: AppContext, arguments: str) -> CommandResult:
    query = arguments.strip()
    if not query:
        raise CommandError("Usage: search contacts <query>")
    results = context.address_book.search(query)
    if not results:
        return CommandResult("No matching contacts.")
    lines = ["Matches:"]
    for record in results:
        lines.append(f"- {record}")
    return CommandResult("\n".join(lines))


def upcoming_birthdays(context: AppContext, arguments: str) -> CommandResult:
    try:
        days = int(arguments.strip())
    except ValueError as exc:
        raise CommandError("Usage: upcoming birthdays <days>") from exc
    today = datetime.today()
    results = context.address_book.upcoming_birthdays(days, today=today)
    if not results:
        return CommandResult("No upcoming birthdays in the selected range.")
    lines = [f"Birthdays within {days} days:"]
    for record in results:
        days_left = record.days_to_birthday(today=today)
        lines.append(f"- {record.name.value}: in {days_left} day(s)")
    return CommandResult("\n".join(lines))


def add_note(context: AppContext, arguments: str) -> CommandResult:
    tokens = shlex.split(arguments)
    if not tokens:
        raise CommandError(
            "Usage: add note <title> content=\"...\" [tags=tag1,tag2]"
        )
    title = tokens[0]
    kv_args = parse_key_value_args(tokens[1:])
    content = kv_args.get("content", "")
    tags = kv_args.get("tags", "")
    note = Note(title=title, content=content)
    if tags:
        note.add_tags(tag.strip() for tag in tags.split(","))
    context.notebook.add(note)
    context.storage.save(context.address_book, context.notebook)
    return CommandResult(f"Note '{title}' added.")


def list_notes(context: AppContext, _: str) -> CommandResult:
    notes = list(context.notebook.values())
    if not notes:
        return CommandResult("No notes yet.")
    lines = ["Notes:"]
    for note in notes:
        tag_string = ", ".join(sorted(note.tags)) or "-"
        lines.append(f"- {note.title} [{tag_string}]")
    return CommandResult("\n".join(lines))


def show_note(context: AppContext, arguments: str) -> CommandResult:
    tokens = shlex.split(arguments)
    if not tokens:
        raise CommandError("Usage: show note <title>")
    title = tokens[0]
    note = context.notebook.get(title)
    if not note:
        raise CommandError(f"Note '{title}' not found.")
    tag_string = ", ".join(sorted(note.tags)) or "-"
    return CommandResult(f"{note.title} [{tag_string}]\n{note.content}")


def edit_note(context: AppContext, arguments: str) -> CommandResult:
    tokens = shlex.split(arguments)
    if not tokens:
        raise CommandError(
            "Usage: edit note <title> [content=\"...\"] [add_tags=tag1,tag2] "
            "[remove_tags=tag]"
        )
    title = tokens[0]
    note = context.notebook.get(title)
    if not note:
        raise CommandError(f"Note '{title}' not found.")
    kv_args = parse_key_value_args(tokens[1:])
    if "content" in kv_args:
        note.content = kv_args["content"]
    if "add_tags" in kv_args:
        note.add_tags(tag.strip() for tag in kv_args["add_tags"].split(","))
    if "remove_tags" in kv_args:
        for tag in kv_args["remove_tags"].split(","):
            note.remove_tag(tag)
    context.storage.save(context.address_book, context.notebook)
    return CommandResult(f"Note '{title}' updated.")


def delete_note(context: AppContext, arguments: str) -> CommandResult:
    tokens = shlex.split(arguments)
    if not tokens:
        raise CommandError("Usage: delete note <title>")
    title = tokens[0]
    if context.notebook.remove(title):
        context.storage.save(context.address_book, context.notebook)
        return CommandResult(f"Note '{title}' deleted.")
    raise CommandError(f"Note '{title}' not found.")


def search_notes(context: AppContext, arguments: str) -> CommandResult:
    query = arguments.strip()
    if not query:
        raise CommandError("Usage: search notes <query>")
    matches = context.notebook.search(query)
    if not matches:
        return CommandResult("No notes match the query.")
    lines = ["Matching notes:"]
    for note in matches:
        tag_string = ", ".join(sorted(note.tags)) or "-"
        lines.append(f"- {note.title} [{tag_string}]")
    return CommandResult("\n".join(lines))


def search_notes_by_tag(context: AppContext, arguments: str) -> CommandResult:
    tag = arguments.strip()
    if not tag:
        raise CommandError("Usage: search notes by tag <tag>")
    matches = context.notebook.search_by_tag(tag)
    if not matches:
        return CommandResult(f"No notes found with tag '{tag}'.")
    lines = [f"Notes with tag '{tag}':"]
    for note in matches:
        lines.append(f"- {note.title}")
    return CommandResult("\n".join(lines))


def sort_notes_by_tags(context: AppContext, _: str) -> CommandResult:
    notes = context.notebook.sorted_by_tags()
    if not notes:
        return CommandResult("No notes to sort.")
    lines = ["Notes sorted by tags:"]
    for note in notes:
        tag_string = ", ".join(sorted(note.tags)) or "-"
        lines.append(f"- [{tag_string}] {note.title}")
    return CommandResult("\n".join(lines))


def exit_command(_: AppContext, __: str) -> CommandResult:
    return CommandResult("Goodbye!", should_exit=True)


def build_command_map() -> Dict[str, tuple[CommandFunc, str]]:
    return {
        "add contact": (add_contact, "add contact John phone=+123 email=john@example.com"),
        "list contacts": (list_contacts, "List all contacts."),
        "show contact": (show_contact, "show contact John"),
        "edit contact": (edit_contact, "edit contact John phone=old:new email=new@example.com"),
        "delete contact": (delete_contact, "delete contact John"),
        "search contacts": (search_contacts, "search contacts John"),
        "upcoming birthdays": (upcoming_birthdays, "upcoming birthdays 7"),
        "add note": (add_note, "add note \"Meeting Notes\" content=\"Discuss roadmap\" tags=work,planning"),
        "list notes": (list_notes, "List all notes."),
        "show note": (show_note, "show note \"Meeting Notes\""),
        "edit note": (edit_note, "edit note \"Meeting Notes\" content=\"Updated\" add_tags=urgent"),
        "delete note": (delete_note, "delete note \"Meeting Notes\""),
        "search notes": (search_notes, "search notes roadmap"),
        "search notes by tag": (search_notes_by_tag, "search notes by tag work"),
        "sort notes by tags": (sort_notes_by_tags, "sort notes by tags"),
        "exit": (exit_command, "Exit the assistant."),
        "quit": (exit_command, "Exit the assistant."),
    }


def suggest_command(user_input: str, command_map: Dict[str, tuple[CommandFunc, str]]) -> Optional[str]:
    if not user_input:
        return None
    
    names = list(command_map.keys())
    
    # Спочатку пробуємо знайти схожість для всього введеного тексту
    matches = get_close_matches(user_input, names, n=1, cutoff=0.5)
    if matches:
        return matches[0]
    
    # Якщо не знайшли, пробуємо витягти частину команди (перші 2-4 слова)
    # Це допоможе, якщо користувач ввів "ad contact John" замість "add contact John"
    words = user_input.split()
    if len(words) > 1:
        # Пробуємо різні комбінації слів (від довших до коротших)
        for word_count in range(min(4, len(words)), 0, -1):
            partial_command = " ".join(words[:word_count])
            matches = get_close_matches(partial_command, names, n=1, cutoff=0.5)
            if matches:
                return matches[0]
    
    return None


