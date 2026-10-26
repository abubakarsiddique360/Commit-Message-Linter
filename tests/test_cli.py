from __future__ import annotations

import json
from pathlib import Path

from commit_message_linter.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_lint_bad_batch(capsys) -> None:
    assert main(["lint", str(EXAMPLES / "commits.txt")]) == 1
    out = capsys.readouterr().out
    assert "unknown-type" in out
    assert "FAIL" in out


def test_lint_clean_batch(capsys) -> None:
    assert main(["lint", str(EXAMPLES / "clean-commits.txt")]) == 0
    assert "PASS" in capsys.readouterr().out


def test_lint_json(capsys) -> None:
    main(["lint", str(EXAMPLES / "commits.txt"), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "fail"
    assert payload["commits"] == 8


def test_lint_min_severity(capsys) -> None:
    main(["lint", str(EXAMPLES / "commits.txt"), "--json", "--min-severity", "error"])
    payload = json.loads(capsys.readouterr().out)
    severities = {finding["severity"] for entry in payload["entries"] for finding in entry["findings"]}
    assert severities == {"error"}


def test_message_command_good(capsys) -> None:
    assert main(["message", "feat(api): add retry"]) == 0
    assert "PASS" in capsys.readouterr().out


def test_message_command_bad(capsys) -> None:
    assert main(["message", "Add stuff."]) == 1
    assert "header-format" in capsys.readouterr().out


def test_message_command_understands_newlines(capsys) -> None:
    assert main(["message", "feat: a\\n\\nBREAKING CHANGE: b"]) == 0
    assert "breaking-note-missing" not in capsys.readouterr().out


def test_changelog_command(capsys) -> None:
    assert main(["changelog", str(EXAMPLES / "clean-commits.txt"), "--version", "v2.0.0"]) == 0
    out = capsys.readouterr().out
    assert "## v2.0.0" in out
    assert "### Features" in out


def test_rules_command(capsys) -> None:
    assert main(["rules"]) == 0
    assert "header-format" in capsys.readouterr().out


def test_missing_file(tmp_path, capsys) -> None:
    assert main(["lint", str(tmp_path / "nope.txt")]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_file_without_commits(tmp_path, capsys) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("   \n\n", encoding="utf-8")
    assert main(["lint", str(path)]) == 2
    assert "no commits" in capsys.readouterr().err
