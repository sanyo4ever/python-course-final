from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Set


@dataclass
class Note:
    title: str
    content: str
    tags: Set[str] = field(default_factory=set)

    def add_tags(self, new_tags: Iterable[str]) -> None:
        self.tags.update({tag.strip().lower() for tag in new_tags if tag.strip()})

    def remove_tag(self, tag: str) -> bool:
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False

    def matches(self, query: str) -> bool:
        query_lower = query.lower()
        in_tags = any(query_lower in tag for tag in self.tags)
        return (
            query_lower in self.title.lower()
            or query_lower in self.content.lower()
            or in_tags
        )

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "tags": sorted(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(
            title=data["title"],
            content=data.get("content", ""),
            tags=set(data.get("tags", [])),
        )


class Notebook(UserDict[str, Note]):
    """Container class for user notes with tag-based search."""

    def add(self, note: Note) -> None:
        self.data[note.title.lower()] = note

    def get(self, title: str) -> Optional[Note]:
        return self.data.get(title.lower())

    def remove(self, title: str) -> bool:
        return self.data.pop(title.lower(), None) is not None

    def search(self, query: str) -> List[Note]:
        query_lower = query.lower()
        return [note for note in self.data.values() if note.matches(query_lower)]

    def search_by_tag(self, tag: str) -> List[Note]:
        tag = tag.strip().lower()
        return sorted(
            (note for note in self.data.values() if tag in note.tags),
            key=lambda note: note.title.lower(),
        )

    def sorted_by_tags(self) -> List[Note]:
        def tag_key(note: Note) -> tuple:
            tag_list = sorted(note.tags) or [""]
            return (tag_list, note.title.lower())

        return sorted(self.data.values(), key=tag_key)

    def to_serializable(self) -> List[dict]:
        return [note.to_dict() for note in self.data.values()]

    @classmethod
    def from_serializable(cls, data: Iterable[dict]) -> "Notebook":
        notebook = cls()
        for entry in data:
            notebook.add(Note.from_dict(entry))
        return notebook


