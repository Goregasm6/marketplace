from app.main import hello


def test_hello_command_runs(capsys):
    hello()
    captured = capsys.readouterr()
    assert "Hello from maie" in captured.out
