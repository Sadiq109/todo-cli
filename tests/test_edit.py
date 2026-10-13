import pytest

from todo_cli.cli import run
from todo_cli.store import TaskStore, TodoError


@pytest.fixture
def store(tmp_path):
    s = TaskStore(tmp_path / "t.json")
    s.add("old title", "low", "2026-10-01", ["a", "b"])
    return s


def test_edit_changes_only_given_fields(store):
    t = store.edit(1, priority="high")
    assert (t.title, t.priority, t.due, t.tags) == ("old title", "high", "2026-10-01", ["a", "b"])


def test_edit_all_fields_and_tags_replace(store):
    t = store.edit(1, title=" new ", priority="MEDIUM", due="2026-12-31", tags=["Z", " "])
    assert (t.title, t.priority, t.due, t.tags) == ("new", "medium", "2026-12-31", ["z"])


def test_clear_due_and_clear_tags(store):
    t = store.edit(1, clear_due=True, tags=[])
    assert t.due is None and t.tags == []


def test_bad_input_changes_nothing(store):
    for kwargs in ({"title": "ok", "due": "nope"}, {"title": "  "}, {"priority": "urgent"}, {"due": "2026-11-01", "clear_due": True}):
        with pytest.raises(TodoError):
            store.edit(1, **kwargs)
    t = store.get(1)
    assert (t.title, t.priority, t.due) == ("old title", "low", "2026-10-01")


def test_unknown_id(store):
    with pytest.raises(TodoError):
        store.edit(9, title="x")


def test_cli_edit_flow_and_errors(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    run(f + ["add", "Call", "bank", "-t", "errands"])
    capsys.readouterr()
    assert run(f + ["edit", "1", "-p", "high", "-d", "2026-10-05", "--title", "Call the bank"]) == 0
    assert "Updated task 1: Call the bank" in capsys.readouterr().out
    assert run(f + ["list"]) == 0
    listed = capsys.readouterr().out
    assert "(high)" in listed and "due 2026-10-05" in listed and "#errands" in listed
    assert run(f + ["edit", "1", "--clear-tags", "--clear-due"]) == 0
    capsys.readouterr()
    assert run(f + ["list"]) == 0
    listed = capsys.readouterr().out
    assert "#errands" not in listed and "due" not in listed
    for bad in (["edit", "1"], ["edit", "1", "-d", "tomorrow"], ["edit", "1", "-t", "x", "--clear-tags"], ["edit", "7", "--title", "x"]):
        assert run(f + bad) == 1
        assert "error:" in capsys.readouterr().err
    assert run(f + ["list"]) == 0
    assert "Call the bank" in capsys.readouterr().out
