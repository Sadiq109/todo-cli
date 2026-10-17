"""Command-line interface for todo-cli."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
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
    ls.add_argument("-s", "--search", metavar="TEXT", help="only tasks whose title contains TEXT (ignores case)")
    ls.add_argument("--json", action="store_true", help="print tasks as a JSON array")
    ls.add_argument("--overdue", action="store_true", help="only open tasks past their due date")
    ls.add_argument("--due-before", metavar="YYYY-MM-DD", help="only tasks due before this date")

    ed = sub.add_parser("edit", help="change a task's title, priority, due date or tags")
    ed.add_argument("id", type=int)
    ed.add_argument("--title", help="new title")
    ed.add_argument("-p", "--priority", choices=PRIORITIES)
    ed.add_argument("-d", "--due", help="new due date, YYYY-MM-DD")
    ed.add_argument("--clear-due", action="store_true", help="remove the due date")
    ed.add_argument("-t", "--tag", action="append", help="replace tags with these (repeatable)")
    ed.add_argument("--clear-tags", action="store_true", help="remove all tags")

    for name, help_text in (("done", "mark a task complete"), ("undo", "mark a task not complete"),
                            ("remove", "delete a task")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("id", type=int)

    sub.add_parser("clear", help="delete all completed tasks")
    sub.add_parser("stats", help="show counts: total, open, done, overdue")
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
            tasks = store.query(show_done=args.all, tag=args.tag, overdue=args.overdue, due_before=args.due_before, text=args.search)
            if args.json:
                print(json.dumps([{**asdict(t), "overdue": t.is_overdue()} for t in tasks], indent=2))
            elif not tasks:
                if args.overdue or args.due_before or args.search:
                    print("No matching tasks.")
                else:
                    print("No tasks. Add one with: todo add \"Buy groceries\"")
            if not args.json:
                for task in tasks:
                    print(format_task(task))
        elif args.command == "edit":
            if args.tag and args.clear_tags:
                raise TodoError("use either --tag or --clear-tags, not both")
            tags = [] if args.clear_tags else args.tag
            if all(v is None or v is False for v in (args.title, args.priority, args.due, args.clear_due, tags)) and tags != []:
                raise TodoError("nothing to change; give --title, --priority, --due, --clear-due, --tag or --clear-tags")
            task = store.edit(args.id, args.title, args.priority, args.due, args.clear_due, tags)
            store.save()
            print(f"Updated task {task.id}: {task.title}")
        elif args.command in ("done", "undo"):
            task = store.set_done(args.id, args.command == "done")
            store.save()
            print(f"Task {task.id} marked {'done' if task.done else 'not done'}.")
        elif args.command == "remove":
            task = store.remove(args.id)
            store.save()
            print(f"Removed task {task.id}: {task.title}")
        elif args.command == "stats":
            s = store.stats()
            print(f"{s['total']} total, {s['open']} open, {s['done']} done, {s['overdue']} overdue")
            print("open by priority: " + ", ".join(f"{p} {n}" for p, n in s["open_by_priority"].items()))
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
