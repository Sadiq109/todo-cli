import json
from datetime import date

import pytest

from todo_cli.store import TaskStore, TodoError


@pytest.fixture
def store(tmp_path):
    return TaskStore(tmp_path / "tasks.json")


def test_add_assigns_increasing_ids_and_persists(store):
    a = store.add("Write report")
    b = store.add("Email advisor", priority="high", due="2026-10-01", tags=["School", "school"])
    store.save()
    reloaded = TaskStore(store.path)
    assert [t.id for t in reloaded.tasks] == [a.id, b.id] == [1, 2]
    assert reloaded.get(2).tags == ["school"]
    assert reloaded.get(2).due == "2026-10-01"


def test_ids_are_not_reused_after_remove(store):
    store.add("one")
    store.add("two")
    store.remove(2)
    assert store.add("three").id == 2
    store.remove(1)
    assert store.add("four").id == 3


def test_rejects_empty_title_bad_priority_and_bad_date(store):
    with pytest.raises(TodoError):
        store.add("   ")
    with pytest.raises(TodoError):
        store.add("x", priority="urgent")
    with pytest.raises(TodoError):
        store.add("x", due="10/01/2026")


def test_unknown_id_raises(store):
    with pytest.raises(TodoError):
        store.set_done(99)


def test_query_orders_by_status_priority_due(store):
    store.add("low", priority="low")
    store.add("high later", priority="high", due="2026-12-01")
    store.add("high sooner", priority="high", due="2026-11-01")
    store.add("finished", priority="high")
    store.set_done(4)
    assert [t.title for t in store.query()] == ["high sooner", "high later", "low"]
    assert store.query(show_done=True)[-1].title == "finished"


def test_filter_by_tag_and_clear_done(store):
    store.add("a", tags=["work"])
    store.add("b", tags=["home"])
    store.set_done(1)
    assert [t.title for t in store.query(show_done=True, tag="WORK")] == ["a"]
    assert store.clear_done() == 1
    assert [t.title for t in store.tasks] == ["b"]


def test_overdue(store):
    task = store.add("pay bill", due="2026-01-01")
    assert task.is_overdue(today=date(2026, 1, 2))
    assert not task.is_overdue(today=date(2025, 12, 31))
    task.done = True
    assert not task.is_overdue(today=date(2026, 1, 2))


def test_corrupt_file_gives_clear_error(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(TodoError, match="could not read"):
        TaskStore(path)


def test_save_writes_valid_json(store):
    store.add("x")
    store.save()
    assert json.loads(store.path.read_text())["tasks"][0]["title"] == "x"
