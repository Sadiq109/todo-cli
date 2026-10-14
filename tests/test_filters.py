from datetime import date

import pytest

from todo_cli.cli import run
from todo_cli.store import TaskStore, TodoError

TODAY = date(2026, 10, 13)


@pytest.fixture
def store(tmp_path):
    s = TaskStore(tmp_path / "t.json")
    s.add("past", due="2026-10-12", tags=["a"])
    s.add("today", due="2026-10-13")
    s.add("later", due="2026-11-01", tags=["a"])
    s.add("nodate")
    s.add("done past", due="2026-10-01")
    s.set_done(5)
    return s


def titles(tasks):
    return [t.title for t in tasks]


def test_overdue_excludes_today_undated_and_done(store):
    assert titles(store.query(overdue=True, today=TODAY)) == ["past"]


def test_due_before_is_exclusive_and_skips_undated(store):
    assert titles(store.query(due_before="2026-10-13")) == ["past"]
    assert titles(store.query(due_before="2026-11-02")) == ["past", "today", "later"]


def test_filters_combine_with_tag_and_all(store):
    assert titles(store.query(due_before="2026-11-02", tag="a")) == ["past", "later"]
    assert titles(store.query(show_done=True, due_before="2026-10-12")) == ["done past"]


def test_bad_cutoff_is_an_error(store):
    with pytest.raises(TodoError):
        store.query(due_before="soon")


def test_cli_filters_and_empty_message(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    run(f + ["add", "x", "-d", "2999-01-01"])
    capsys.readouterr()
    assert run(f + ["list", "--overdue"]) == 0
    assert "No matching tasks." in capsys.readouterr().out
    assert run(f + ["list", "--due-before", "3000-01-01"]) == 0
    assert "x" in capsys.readouterr().out
    assert run(f + ["list", "--due-before", "soon"]) == 1
    assert "error:" in capsys.readouterr().err
