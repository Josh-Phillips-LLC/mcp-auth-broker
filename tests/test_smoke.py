from mcp_auth_broker import main


def test_main_runs(capsys):
    main()
    captured = capsys.readouterr()
    assert "bootstrap ready" in captured.out
