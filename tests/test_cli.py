from todo_cli.cli import run


def test_full_workflow(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    assert run(f + ["add", "Buy", "groceries", "-p", "high", "-t", "home"]) == 0
    assert run(f + ["add", "Study", "for", "exam", "-d", "2026-12-10"]) == 0
    assert run(f + ["done", "1"]) == 0
    capsys.readouterr()
    assert run(f + ["list"]) == 0
    out = capsys.readouterr().out
    assert "Study for exam" in out and "Buy groceries" not in out
    assert run(f + ["list", "--all"]) == 0
    assert "[x] Buy groceries" in capsys.readouterr().out
    assert run(f + ["clear"]) == 0
    assert "Cleared 1 completed task." in capsys.readouterr().out


def test_errors_return_nonzero(tmp_path, capsys):
    f = ["--file", str(tmp_path / "t.json")]
    assert run(f + ["done", "5"]) == 1
    assert "no task with id 5" in capsys.readouterr().err
    assert run(f + ["add", "x", "-d", "tomorrow"]) == 1


def test_uses_env_var(tmp_path, monkeypatch, capsys):
    path = tmp_path / "env.json"
    monkeypatch.setenv("TODO_FILE", str(path))
    assert run(["add", "from env"]) == 0
    assert path.exists()
