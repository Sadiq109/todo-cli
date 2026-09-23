"""Command-line interface for todo-cli."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .store import PRIORITIES, Task, TaskStore, TodoError

DEFAULT_FILE = Path.home() / ".todo.json"


def format_task(task: Task) -> str:
    box = "[x]" if task.done else "[ ]"
    parts = [f"{task.id:>3} {box} {task.title}", f"({task.priority})"]
    if task.due:
        parts.append(f"due {task.due}" + (" OVERDUE" if task.is_overdue() else ""))
    if task.tags:
        parts.append(" ".join(f"#{t}" for t in task.tags))
    return "  ".join(parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="A small command-line to-do list.")
    parser.add_argument("--file", type=Path, help="task file (default: $TODO_FILE or ~/.todo.json)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a task")
    add.add_argument("title", nargs="+", help="task title")
    add.add_argument("-p", "--priority", default="medium", choices=PRIORITIES)
    add.add_argument("-d", "--due", help="due date, YYYY-MM-DD")
    add.add_argument("-t", "--tag", action="append", default=[], help="tag (repeatable)")

    ls = sub.add_parser("list", help="list tasks")
    ls.add_argument("-a", "--all", action="store_true", help="include completed tasks")
    ls.add_argument("-t", "--tag", help="only tasks with this tag")

    for name, help_text in (("done", "mark a task complete"), ("undo", "mark a task not complete"),
                            ("remove", "delete a task")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("id", type=int)

    sub.add_parser("clear", help="delete all completed tasks")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = args.file or Path(os.environ.get("TODO_FILE", DEFAULT_FILE))
    try:
        store = TaskStore(path)
        if args.command == "add":
            task = store.add(" ".join(args.title), args.priority, args.due, args.tag)
            store.save()
            print(f"Added task {task.id}: {task.title}")
        elif args.command == "list":
            tasks = store.query(show_done=args.all, tag=args.tag)
            if not tasks:
                print("No tasks. Add one with: todo add \"Buy groceries\"")
            for task in tasks:
                print(format_task(task))
        elif args.command in ("done", "undo"):
            task = store.set_done(args.id, args.command == "done")
            store.save()
            print(f"Task {task.id} marked {'done' if task.done else 'not done'}.")
        elif args.command == "remove":
            task = store.remove(args.id)
            store.save()
            print(f"Removed task {task.id}: {task.title}")
        elif args.command == "clear":
            count = store.clear_done()
            store.save()
            print(f"Cleared {count} completed task{'s' if count != 1 else ''}.")
    except TodoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
