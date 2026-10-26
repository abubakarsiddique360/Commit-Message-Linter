from __future__ import annotations

from pathlib import Path

import pytest

from commit_message_linter.messages import parse_commits, parse_message

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_simple_header() -> None:
    message = parse_message("feat(api): add retry")
    assert message.matched
    assert message.type == "feat"
    assert message.scope == "api"
    assert message.subject == "add retry"
    assert message.body == ""
    assert message.breaking is False


def test_header_without_scope() -> None:
    message = parse_message("fix: handle empty header")
    assert message.scope is None
    assert message.subject == "handle empty header"


def test_bang_marks_breaking() -> None:
    assert parse_message("feat!: drop v1").breaking is True


def test_breaking_footer_is_detected() -> None:
    message = parse_message("feat: drop v1\n\nBREAKING CHANGE: use v2 instead")
    assert message.breaking is True
    assert message.footers[0].normalised == "BREAKING CHANGE"


def test_body_and_footer_are_split() -> None:
    message = parse_message("fix: a\n\nFirst paragraph.\n\nSecond paragraph.\n\nRefs: #12")
    assert "Second paragraph." in message.body
    assert "Refs" not in message.body
    assert message.footer == "Refs: #12"
    assert message.footers[0].value == "#12"


def test_reference_style_footer() -> None:
    message = parse_message("fix: a\n\nReviewed-by #42")
    assert message.footers[0].value == "#42"


def test_attached_body_flag() -> None:
    assert parse_message("fix: a\nbody right here").attached_body is True
    assert parse_message("fix: a\n\nbody after blank").attached_body is False


def test_unmatched_header_keeps_text_as_subject() -> None:
    message = parse_message("Update the readme")
    assert message.matched is False
    assert message.header == "Update the readme"
    assert message.subject == "Update the readme"


def test_empty_message() -> None:
    message = parse_message("   \n\n")
    assert message.header == ""
    assert message.matched is False


def test_crlf_is_normalised() -> None:
    message = parse_message("fix: a\r\n\r\nbody\r\n")
    assert message.body == "body"


def test_as_dict_shape() -> None:
    payload = parse_message("feat(ui): add").as_dict()
    assert payload["type"] == "feat"
    assert payload["scope"] == "ui"
    assert payload["breaking"] is False


def test_parse_commits_splits_on_separator() -> None:
    text = (EXAMPLES / "clean-commits.txt").read_text(encoding="utf-8")
    commits = parse_commits(text)
    assert len(commits) == 5
    assert [commit.type for commit in commits] == ["feat", "fix", "docs", "feat", "perf"]


def test_parse_commits_ignores_trailing_separator() -> None:
    assert len(parse_commits("feat: a\n---\n\n")) == 1


def test_single_message_file_is_one_commit() -> None:
    assert len(parse_commits("fix: a\n")) == 1


@pytest.mark.parametrize("text", ["", "   "])
def test_parse_commits_empty(text: str) -> None:
    assert parse_commits(text) == []
