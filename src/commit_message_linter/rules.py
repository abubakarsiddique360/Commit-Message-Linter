"""The rule catalogue for conventional commit messages."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from commit_message_linter.messages import TYPES, CommitMessage

SEVERITIES = ("error", "warning", "note")
SEVERITY_ORDER = {severity: index for index, severity in enumerate(SEVERITIES)}
SCOPE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
STARTS_UPPER_RE = re.compile(r"^[A-Z]")
LOWERCASE_TOKEN_RE = re.compile(r"^[a-z][a-z-]*$")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str

    def as_dict(self) -> dict:
        return {"rule": self.rule, "severity": self.severity, "message": self.message}


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    summary: str
    check: Callable[[CommitMessage], str | None]


def _empty(message: CommitMessage) -> str | None:
    return "the message is empty" if not message.header else None


def _header_format(message: CommitMessage) -> str | None:
    if message.header and not message.matched:
        return "header is not 'type(scope): subject'"
    return None


def _type_case(message: CommitMessage) -> str | None:
    if message.matched and message.type != message.type.lower():
        return f"type '{message.type}' should be lowercase"
    return None


def _unknown_type(message: CommitMessage) -> str | None:
    if message.matched and message.type.lower() not in TYPES:
        return f"type '{message.type}' is not one of {', '.join(TYPES)}"
    return None


def _subject_empty(message: CommitMessage) -> str | None:
    if message.matched and not message.subject:
        return "the subject after the colon is empty"
    return None


def _scope_empty(message: CommitMessage) -> str | None:
    if message.scope is not None and not message.scope.strip():
        return "an empty scope '()' should be removed entirely"
    return None


def _scope_format(message: CommitMessage) -> str | None:
    if message.scope and not SCOPE_RE.match(message.scope):
        return f"scope '{message.scope}' should be lowercase words joined by '-'"
    return None


def _header_too_long(message: CommitMessage) -> str | None:
    if len(message.header) > 72:
        return f"header is {len(message.header)} characters, keep it at 72 or fewer"
    return None


def _subject_trailing_period(message: CommitMessage) -> str | None:
    if message.subject.endswith("."):
        return "the subject should not end with a period"
    return None


def _subject_capitalised(message: CommitMessage) -> str | None:
    if STARTS_UPPER_RE.match(message.subject):
        return "the subject should start in lowercase (imperative mood)"
    return None


def _attached_body(message: CommitMessage) -> str | None:
    if message.attached_body:
        return "leave a blank line between the header and the body"
    return None


def _body_line_too_long(message: CommitMessage) -> str | None:
    for line in message.body.splitlines():
        if len(line) > 100:
            return f"body has a {len(line)} character line, wrap at 100"
    return None


def _breaking_note_missing(message: CommitMessage) -> str | None:
    if message.breaking and not any(
        footer.normalised in {"BREAKING CHANGE", "BREAKING-CHANGE"} for footer in message.footers
    ):
        return "'!' marks a breaking change, add a 'BREAKING CHANGE:' footer explaining it"
    return None


def _footer_token_case(message: CommitMessage) -> str | None:
    for footer in message.footers:
        if footer.normalised in {"BREAKING CHANGE", "BREAKING-CHANGE"}:
            continue
        if not LOWERCASE_TOKEN_RE.match(footer.token) and "-" not in footer.token:
            return f"footer token '{footer.token}' should be lowercase with hyphens"
    return None


def _revert_reference(message: CommitMessage) -> str | None:
    if message.type.lower() != "revert":
        return None
    text = f"{message.body}\n{message.footer}"
    if "This reverts commit" in text or any(footer.normalised == "REFS" for footer in message.footers):
        return None
    return "a revert should reference the original commit"


RULES: tuple[Rule, ...] = (
    Rule("empty-message", "error", "The message has no content at all.", _empty),
    Rule("header-format", "error", "Header must be 'type(scope): subject'.", _header_format),
    Rule("unknown-type", "error", "Type must be one of the conventional types.", _unknown_type),
    Rule("subject-empty", "error", "A header without a subject says nothing.", _subject_empty),
    Rule("scope-empty", "error", "An empty '()' scope is noise.", _scope_empty),
    Rule("type-case", "warning", "Types are written in lowercase.", _type_case),
    Rule("scope-format", "warning", "Scopes use lowercase words joined by hyphens.", _scope_format),
    Rule("header-too-long", "warning", "Headers over 72 characters get truncated in git log.", _header_too_long),
    Rule(
        "subject-trailing-period",
        "warning",
        "Subjects are titles, not sentences.",
        _subject_trailing_period,
    ),
    Rule("subject-capitalised", "warning", "The subject reads best in lowercase.", _subject_capitalised),
    Rule("attached-body", "warning", "A blank line keeps the body out of the subject.", _attached_body),
    Rule("body-line-too-long", "warning", "Long body lines are hard to read in a terminal.", _body_line_too_long),
    Rule(
        "breaking-note-missing",
        "warning",
        "A breaking change needs a footer that explains the migration.",
        _breaking_note_missing,
    ),
    Rule("footer-token-case", "note", "Footer tokens are lowercase with hyphens.", _footer_token_case),
    Rule("revert-reference", "warning", "A revert should point at the commit it undoes.", _revert_reference),
)

RULES_BY_ID = {rule.id: rule for rule in RULES}


def lint(message: CommitMessage) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        problem = rule.check(message)
        if problem:
            findings.append(Finding(rule=rule.id, severity=rule.severity, message=problem))
    findings.sort(key=lambda finding: SEVERITY_ORDER[finding.severity])
    return findings
