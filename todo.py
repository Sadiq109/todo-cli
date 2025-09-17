"""Simple command‑line to‑do list manager.

This script provides a minimalistic to‑do list manager that lets you add
tasks, list current tasks and mark tasks as completed. Tasks are stored in
a plain text file (one per line). Completed tasks are prefixed with a
``[x]`` marker.

Usage:

    python3 todo.py add "Buy groceries"
    python3 todo.py list
    python3 todo.py done 2

The script will create a ``tasks.txt`` file in the current directory to
persist your tasks between runs.
"""

import argparse
from pathlib import Path

TASKS_FILE = Path('tasks.txt')


def load_tasks() -> list[str]:
    """Load tasks from the tasks file, returning a list of task strings."""
    if TASKS_FILE.exists():
        with TASKS_FILE.open('r', encoding='utf-8') as f:
            return [line.rstrip('\n') for line in f]
    return []


def save_tasks(tasks: list[str]) -> None:
    """Persist tasks to the tasks file."""
    with TASKS_FILE.open('w', encoding='utf-8') as f:
        for task in tasks:
            f.write(f"{task}\n")


def add_task(description: str) -> None:
    tasks = load_tasks()
    tasks.append(description)
    save_tasks(tasks)
    print(f'Added task: {description}')


def list_tasks() -> None:
    tasks = load_tasks()
    if not tasks:
        print('No tasks found. Use the "add" command to add a task.')
        return
    for idx, task in enumerate(tasks, start=1):
        print(f"{idx}. {task}")


def complete_task(index: int) -> None:
    tasks = load_tasks()
    if 1 <= index <= len(tasks):
        task = tasks[index - 1]
        tasks[index - 1] = f"[x] {task}"
        save_tasks(tasks)
        print(f'Marked task #{index} as completed.')
    else:
        print(f'Invalid task number: {index}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Simple command‑line to‑do list')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('description', help='Description of the task')

    # List command
    subparsers.add_parser('list', help='List all tasks')

    # Done command
    done_parser = subparsers.add_parser('done', help='Mark a task as completed')
    done_parser.add_argument('index', type=int, help='Task number to mark as completed')

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == 'add':
        add_task(args.description)
    elif args.command == 'list':
        list_tasks()
    elif args.command == 'done':
        complete_task(args.index)
    else:
        print('Please provide a valid command (add, list, done).')


if __name__ == '__main__':
    main()
