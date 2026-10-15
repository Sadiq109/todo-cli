# todo-cli

[![CI](https://github.com/Sadiq109/todo-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/Sadiq109/todo-cli/actions/workflows/ci.yml)

I built this small command-line to-do list in Python. Tasks have priorities, optional due dates and tags, and they're saved to a JSON file so they persist between runs.

## Features

- `add`, `list`, `edit`, `done`, `undo`, `remove` and `clear` commands
- Priorities (`low`, `medium`, `high`), due dates with overdue warnings, and tags
- The list is sorted by open vs. done, then priority, then due date
- Stable task ids that are never reused, even after you remove the newest task
- Atomic saves: the file is written to a temp file first and then swapped in, so a crash can't leave half a file
- Clear error messages and a non-zero exit code for bad ids, bad dates or a corrupt file
- No dependencies outside the standard library, plus tests and CI on Python 3.10 and 3.12

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Usage

```text
$ todo add "Finish lab report" -p high -d 2026-10-02 -t school
Added task 1: Finish lab report
$ todo add Call the bank -t errands
Added task 2: Call the bank
$ todo list
  1 [ ] Finish lab report  (high)  due 2026-10-02  #school
  2 [ ] Call the bank  (medium)  #errands
$ todo edit 2 -p high -d 2026-10-05 --title "Call the bank about the card"
Updated task 2: Call the bank about the card
$ todo done 1
Task 1 marked done.
$ todo list --all --tag school
  1 [x] Finish lab report  (high)  due 2026-10-02  #school
$ todo clear
Cleared 1 completed task.
```

`edit` changes only the fields you give and checks them all first, so a bad date never leaves a half-edited task. `--clear-due` removes the due date, `-t` replaces the tags, and `--clear-tags` removes them.

`list --overdue` shows open tasks past their due date, and `list --due-before 2026-11-01` shows tasks due before that day (the day itself is excluded; tasks with no due date never match). They combine with `--tag` and `--all`.

`list --json` prints the same filtered, sorted tasks as a JSON array (id, title, priority, due, done, tags, and a computed `overdue` flag) for scripts. An empty result is `[]`, never plain text.

Tasks are stored in `~/.todo.json` by default. Use `--file path.json` or set `TODO_FILE` to point somewhere else.

## Tests

```bash
pytest
```

## Project layout

```text
src/todo_cli/store.py   task model, validation, sorting and JSON storage
src/todo_cli/cli.py     argparse commands and output formatting
tests/                  unit tests for the store and end-to-end CLI tests
```
