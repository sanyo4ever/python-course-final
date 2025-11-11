from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, Tuple

from .commands import (
    AppContext,
    CommandError,
    CommandFunc,
    CommandResult,
    build_command_map,
    suggest_command,
)
from .storage import Storage


HELP_HEADER = """Available commands:
- help — show this message.
- commands — list all commands with examples.
"""


@dataclass
class CommandRegistry:
    command_map: Dict[str, Tuple[CommandFunc, str]]

    def resolve(self, user_input: str) -> tuple[str, CommandFunc, str, str]:
        normalized = user_input.strip()
        lowered = normalized.lower()
        for command_name in sorted(self.command_map.keys(), key=len, reverse=True):
            if lowered.startswith(command_name):
                handler, description = self.command_map[command_name]
                arguments = normalized[len(command_name) :].strip()
                return command_name, handler, description, arguments
        raise KeyError

    def help_text(self) -> str:
        lines = ["Commands:"]
        for name, (_, description) in self.command_map.items():
            lines.append(f"- {name}: {description}")
        return "\n".join(lines)


class PersonalAssistantCLI:
    def __init__(self, storage: Storage | None = None) -> None:
        self.storage = storage or Storage()
        address_book, notebook = self.storage.load()
        self.context = AppContext(
            address_book=address_book,
            notebook=notebook,
            storage=self.storage,
        )
        self.registry = CommandRegistry(build_command_map())

    def run(self) -> int:
        print("Welcome to Personal Assistant CLI!")
        print("Type 'help' to see available commands.")
        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                return 0

            if not user_input:
                continue

            lowered = user_input.lower()
            if lowered in {"help", "h"}:
                print(HELP_HEADER.rstrip())
                print(self.registry.help_text())
                continue
            if lowered in {"commands", "?"}:
                print(self.registry.help_text())
                continue

            try:
                name, handler, _, arguments = self.registry.resolve(user_input)
            except KeyError:
                suggestion = suggest_command(lowered, self.registry.command_map)
                if suggestion:
                    print(f"Unknown command. Did you mean '{suggestion}'?")
                else:
                    print("Unknown command. Type 'help' to list available commands.")
                continue

            try:
                result = handler(self.context, arguments)
            except CommandError as error:
                print(f"Error: {error}")
                continue
            except Exception as error:  # pragma: no cover
                print(f"Unexpected error: {error}")
                continue

            print(result.message)
            if result.should_exit:
                return 0


def main() -> int:
    cli = PersonalAssistantCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())


