from __future__ import annotations

import pytest

from commit_message_linter.messages import parse_message
from commit_message_linter.rules import RULES, RULES_BY_ID, SEVERITY_ORDER, lint


def ids(text: str) -> set[str]:
    return {finding.rule for finding in lint(parse_message(text))}


def test_clean_message_has_no_findings() -> None:
    assert lint(parse_message("feat(api): add retry backoff")) == []


def test_empty_message() -> None:
    assert ids("") == {"empty-message"}


def test_header_without_type() -> None:
    assert "header-format" in ids("Update the readme")


def test_unknown_type() -> None:
    assert "unknown-type" in ids("feature: add thing")


def test_type_case() -> None:
    assert "type-case" in ids("Feat: add thing")


def test_subject_empty() -> None:
    assert "subject-empty" in ids("feat:   ")


def test_scope_empty() -> None:
    assert "scope-empty" in ids("feat(): add thing")


def test_scope_format() -> None:
    assert "scope-format" in ids("feat(API Layer): add thing")
    assert "scope-format" not in ids("feat(api-layer): add thing")


def test_header_too_long() -> None:
    assert "header-too-long" in ids("feat: " + "a" * 80)


def test_trailing_period() -> None:
    assert "subject-trailing-period" in ids("fix: stop the loop.")


def test_capitalised_subject() -> None:
    assert "subject-capitalised" in ids("fix: Stop the loop")


def test_attached_body() -> None:
    assert "attached-body" in ids("fix: stop the loop\nBecause it hangs.")


def test_body_line_too_long() -> None:
    assert "body-line-too-long" in ids("fix: stop the loop\n\n" + "x" * 120)


def test_breaking_note_missing() -> None:
    assert "breaking-note-missing" in ids("feat!: drop v1")
    assert "breaking-note-missing" not in ids("feat!: drop v1\n\nBREAKING CHANGE: move to v2")


def test_footer_token_case() -> None:
    assert "footer-token-case" in ids("fix: a\n\nSigned Off By: someone")
    assert "footer-token-case" not in ids("fix: a\n\nsigned-off-by: someone")


def test_revert_reference() -> None:
    assert "revert-reference" in ids("revert: undo the parser change")
    assert "revert-reference" not in ids("revert: undo\n\nThis reverts commit abc123.")


def test_findings_are_sorted_by_severity() -> None:
    found = lint(parse_message("feature(API): Add The Endpoint."))
    severities = [SEVERITY_ORDER[finding.severity] for finding in found]
    assert severities == sorted(severities)
    assert found[0].severity == "error"


def test_rules_are_unique_and_documented() -> None:
    assert len({rule.id for rule in RULES}) == len(RULES)
    assert all(rule.summary and rule.severity in SEVERITY_ORDER for rule in RULES)
    assert RULES_BY_ID["unknown-type"].severity == "error"


@pytest.mark.parametrize("message", ["feat: a", "fix(ui): b", "docs: c", "chore(deps): d", "ci: e"])
def test_common_good_messages_pass(message: str) -> None:
    assert lint(parse_message(message)) == []
