import json

from todo_cli.cli import run


def test_list_json_fields_filters_and_order(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    run(f + ["add", "low one", "-p", "low", "-t", "x"])
    run(f + ["add", "high one", "-p", "high", "-d", "2000-01-01"])
    run(f + ["add", "done one"])
    run(f + ["done", "3"])
    capsys.readouterr()
    assert run(f + ["list", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [t["title"] for t in data] == ["high one", "low one"]
    assert data[0] == {"id": 2, "title": "high one", "priority": "high", "due": "2000-01-01", "done": False, "tags": [], "overdue": True}
    assert data[1]["overdue"] is False and data[1]["tags"] == ["x"]
    assert run(f + ["list", "--json", "--all", "--tag", "x"]) == 0
    assert [t["id"] for t in json.loads(capsys.readouterr().out)] == [1]


def test_empty_results_are_valid_json_and_text_mode_unchanged(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    assert run(f + ["list", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []
    assert run(f + ["list"]) == 0
    assert "No tasks." in capsys.readouterr().out
    run(f + ["add", "x"])
    capsys.readouterr()
    assert run(f + ["list", "--json", "--overdue"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_json_mode_errors_still_go_to_stderr(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    assert run(f + ["list", "--json", "--due-before", "soon"]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and "error:" in captured.err
