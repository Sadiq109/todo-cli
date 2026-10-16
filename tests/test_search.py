import json

import pytest

from todo_cli.cli import run
from todo_cli.store import TaskStore


@pytest.fixture
def store(tmp_path):
    s = TaskStore(tmp_path / "t.json")
    s.add("Call the Bank", tags=["errands"])
    s.add("bank statement review", due="2026-10-01")
    s.add("Buy milk")
    s.add("Archive bank notes")
    s.set_done(4)
    return s


def titles(tasks):
    return [t.title for t in tasks]


def test_search_ignores_case_and_matches_substrings(store):
    assert titles(store.query(text="BANK")) == ["bank statement review", "Call the Bank"]
    assert titles(store.query(text="ilk")) == ["Buy milk"]


def test_search_respects_done_and_other_filters(store):
    assert titles(store.query(text="bank", show_done=True))[-1] == "Archive bank notes"
    assert titles(store.query(text="bank", tag="errands")) == ["Call the Bank"]
    assert titles(store.query(text="bank", due_before="2026-12-01")) == ["bank statement review"]


def test_blank_search_means_no_filter_and_no_match_is_empty(store):
    assert len(store.query(text="  ")) == 3
    assert store.query(text="zzz") == []


def test_cli_search_text_and_json(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    run(f + ["add", "Pay rent"])
    run(f + ["add", "Call bank"])
    capsys.readouterr()
    assert run(f + ["list", "-s", "BANK"]) == 0
    out = capsys.readouterr().out
    assert "Call bank" in out and "Pay rent" not in out
    assert run(f + ["list", "--search", "nothing"]) == 0
    assert "No matching tasks." in capsys.readouterr().out
    assert run(f + ["list", "--search", "rent", "--json"]) == 0
    assert [t["title"] for t in json.loads(capsys.readouterr().out)] == ["Pay rent"]
