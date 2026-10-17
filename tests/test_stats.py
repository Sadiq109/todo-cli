from datetime import date

from todo_cli.cli import run
from todo_cli.store import TaskStore

TODAY = date(2026, 10, 16)


def make_store(tmp_path):
    s = TaskStore(tmp_path / "t.json")
    s.add("overdue high", priority="high", due="2026-10-10")
    s.add("open low", priority="low")
    s.add("open medium", priority="medium", due="2026-10-16")  # due today is not overdue
    s.add("finished", priority="high", due="2026-10-01")
    s.set_done(4)
    return s


def test_stats_counts(tmp_path):
    s = make_store(tmp_path)
    assert s.stats(today=TODAY) == {
        "total": 4,
        "open": 3,
        "done": 1,
        "overdue": 1,
        "open_by_priority": {"low": 1, "medium": 1, "high": 1},
    }


def test_stats_done_tasks_are_never_overdue(tmp_path):
    s = TaskStore(tmp_path / "t.json")
    s.add("old", due="2020-01-01")
    s.set_done(1)
    stats = s.stats(today=TODAY)
    assert stats["overdue"] == 0
    assert stats["done"] == 1


def test_stats_empty_list(tmp_path):
    s = TaskStore(tmp_path / "t.json")
    assert s.stats(today=TODAY) == {
        "total": 0,
        "open": 0,
        "done": 0,
        "overdue": 0,
        "open_by_priority": {"low": 0, "medium": 0, "high": 0},
    }


def test_cli_stats(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    run(f + ["add", "a", "-p", "high"])
    run(f + ["add", "b"])
    run(f + ["done", "1"])
    capsys.readouterr()
    assert run(f + ["stats"]) == 0
    out = capsys.readouterr().out
    assert "2 total, 1 open, 1 done, 0 overdue" in out
    assert "low 0, medium 1, high 0" in out
