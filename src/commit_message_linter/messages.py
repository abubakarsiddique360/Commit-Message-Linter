"""Split a commit message into header, body and footer."""

from __future__ import annotations

import re
from dataclasses import dataclass

TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)

HEADER_RE = re.compile(r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^()]*)\))?(?P<breaking>!)?:[ \t]*(?P<subject>.*)$")
FOOTER_RE = re.compile(r"^(?P<token>[A-Za-z][A-Za-z _-]*?):[ \t]+(?P<value>\S.*)$")
FOOTER_REF_RE = re.compile(r"^(?P<token>[A-Za-z][A-Za-z _-]*?)[ \t]+#(?P<value>\d+)$")
BREAKING_TOKENS = frozenset({"BREAKING CHANGE", "BREAKING-CHANGE"})
BLOCK_SEPARATOR_RE = re.compile(r"(?m)^---[ \t]*$")


@dataclass(frozen=True)
class Footer:
    token: str
    value: str

    @property
    def normalised(self) -> str:
        return self.token.strip().upper()


@dataclass(frozen=True)
class CommitMessage:
    raw: str
    header: str = ""
    body: str = ""
    footer: str = ""
    type: str = ""
    scope: str | None = None
    subject: str = ""
    breaking: bool = False
    footers: tuple[Footer, ...] = ()
    attached_body: bool = False

    @property
    def matched(self) -> bool:
        return bool(self.type)

    @property
    def subject_length(self) -> int:
        return len(self.subject)

    def as_dict(self) -> dict:
        return {
            "type": self.type,
            "scope": self.scope,
            "subject": self.subject,
            "breaking": self.breaking,
            "header": self.header,
            "body": self.body,
            "footer": self.footer,
        }


def _paragraphs(lines: list[str]) -> list[list[str]]:
    paragraphs: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line)
        elif current:
            paragraphs.append(current)
            current = []
    if current:
        paragraphs.append(current)
    return paragraphs


def _footer_of(line: str) -> Footer | None:
    match = FOOTER_RE.match(line)
    if match:
        return Footer(token=match.group("token"), value=match.group("value"))
    match = FOOTER_REF_RE.match(line)
    if match:
        return Footer(token=match.group("token"), value=f"#{match.group('value')}")
    return None


def _footer_block(lines: list[str]) -> tuple[Footer, ...] | None:
    footers = [_footer_of(line) for line in lines]
    if any(footer is None for footer in footers):
        return None
    return tuple(footer for footer in footers if footer is not None)


def parse_message(text: str) -> CommitMessage:
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalised.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines or not lines[0].strip():
        return CommitMessage(raw=text)

    header = lines[0].strip()
    rest = lines[1:]
    attached = bool(rest) and bool(rest[0].strip())

    paragraphs = _paragraphs(rest)
    footer_text = ""
    footers: tuple[Footer, ...] = ()
    if paragraphs:
        candidate = _footer_block(paragraphs[-1])
        if candidate is not None:
            footers = candidate
            footer_text = "\n".join(paragraphs[-1])
            paragraphs = paragraphs[:-1]
    body = "\n\n".join("\n".join(paragraph) for paragraph in paragraphs)

    match = HEADER_RE.match(header)
    breaking = any(footer.normalised in BREAKING_TOKENS for footer in footers)
    if not match:
        return CommitMessage(
            raw=text,
            header=header,
            body=body,
            footer=footer_text,
            subject=header,
            breaking=breaking,
            footers=footers,
            attached_body=attached,
        )

    scope = match.group("scope")
    return CommitMessage(
        raw=text,
        header=header,
        body=body,
        footer=footer_text,
        type=match.group("type"),
        scope=scope,
        subject=match.group("subject").strip(),
        breaking=breaking or bool(match.group("breaking")),
        footers=footers,
        attached_body=attached,
    )


def parse_commits(text: str) -> list[CommitMessage]:
    """Read a batch file where commits are separated by a line containing only `---`."""
    blocks = BLOCK_SEPARATOR_RE.split(text)
    return [parse_message(block) for block in blocks if block.strip()]
