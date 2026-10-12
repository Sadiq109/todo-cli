import json

from todo_cli.cli import run
from todo_cli.store import TaskStore, TodoError


def test_removed_newest_id_is_not_reused(tmp_path):
    path = tmp_path / "t.json"
    store = TaskStore(path)
    store.add("one")
    store.add("two")
    store.remove(2)
    store.save()
    assert TaskStore(path).add("three").id == 3


def test_id_not_reused_within_one_session(tmp_path):
    store = TaskStore(tmp_path / "t.json")
    store.add("one")
    store.remove(1)
    assert store.add("two").id == 2


def test_old_files_without_next_id_still_load(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"tasks": [{"id": 7, "title": "legacy"}]}), encoding="utf-8")
    assert TaskStore(path).add("new").id == 8


def test_bad_next_id_is_a_clean_error(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"next_id": "x", "tasks": []}), encoding="utf-8")
    try:
        TaskStore(path)
    except TodoError as exc:
        assert "next_id" in str(exc)
    else:
        raise AssertionError("expected TodoError")
    assert run(["--file", str(path), "list"]) == 1
    assert "error:" in capsys.readouterr().err


def test_cli_remove_then_add_gives_fresh_id(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    run(f + ["add", "a"])
    run(f + ["add", "b"])
    run(f + ["remove", "2"])
    capsys.readouterr()
    run(f + ["add", "c"])
    assert "Added task 3: c" in capsys.readouterr().out
