"""Task model and JSON-backed storage."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

PRIORITIES = ("low", "medium", "high")


class TodoError(Exception):
    """Raised for user-facing errors such as a bad task id or a corrupt file."""


@dataclass
class Task:
    id: int
    title: str
    priority: str = "medium"
    due: str | None = None
    done: bool = False
    tags: list[str] = field(default_factory=list)

    def is_overdue(self, today: date | None = None) -> bool:
        if self.done or not self.due:
            return False
        return date.fromisoformat(self.due) < (today or date.today())


def validate_priority(value: str) -> str:
    value = value.lower()
    if value not in PRIORITIES:
        raise TodoError(f"priority must be one of: {', '.join(PRIORITIES)}")
    return value


def validate_due(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise TodoError(f"due date must look like YYYY-MM-DD, got {value!r}") from None


class TaskStore:
    """Loads and saves tasks to a JSON file. Writes are atomic."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.tasks: list[Task] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.tasks = [Task(**item) for item in raw.get("tasks", [])]
        except (json.JSONDecodeError, TypeError, AttributeError) as exc:
            raise TodoError(f"could not read {self.path}: {exc}") from None

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"tasks": [asdict(t) for t in self.tasks]}
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".todo-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, self.path)

    def _next_id(self) -> int:
        return max((t.id for t in self.tasks), default=0) + 1

    def get(self, task_id: int) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise TodoError(f"no task with id {task_id}")

    def add(self, title: str, priority: str = "medium", due: str | None = None,
            tags: list[str] | None = None) -> Task:
        title = title.strip()
        if not title:
            raise TodoError("task title cannot be empty")
        task = Task(
            id=self._next_id(),
            title=title,
            priority=validate_priority(priority),
            due=validate_due(due),
            tags=sorted({t.strip().lower() for t in (tags or []) if t.strip()}),
        )
        self.tasks.append(task)
        return task

    def set_done(self, task_id: int, done: bool = True) -> Task:
        task = self.get(task_id)
        task.done = done
        return task

    def remove(self, task_id: int) -> Task:
        task = self.get(task_id)
        self.tasks.remove(task)
        return task

    def clear_done(self) -> int:
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if not t.done]
        return before - len(self.tasks)

    def query(self, show_done: bool = False, tag: str | None = None) -> list[Task]:
        """Open tasks first, then by priority (high first), due date, and id."""
        rank = {p: i for i, p in enumerate(reversed(PRIORITIES))}
        items = [t for t in self.tasks if show_done or not t.done]
        if tag:
            items = [t for t in items if tag.lower() in t.tags]
        return sorted(items, key=lambda t: (t.done, rank[t.priority], t.due or "9999-12-31", t.id))
