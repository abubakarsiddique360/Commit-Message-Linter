"""Score a batch of commit messages and render the result."""

from __future__ import annotations

from dataclasses import dataclass, field

from commit_message_linter.messages import CommitMessage
from commit_message_linter.rules import SEVERITY_ORDER, Finding, lint

PENALTY = {"error": 25, "warning": 6, "note": 2}


@dataclass(frozen=True)
class Entry:
    index: int
    commit: CommitMessage
    findings: tuple[Finding, ...]

    @property
    def label(self) -> str:
        return self.commit.header or "<empty message>"


@dataclass
class CommitLintReport:
    commits: list[CommitMessage]
    source: str = "commits"
    entries: tuple[Entry, ...] = field(init=False, default=())
    findings: list[Finding] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.entries = tuple(
            Entry(index=index, commit=commit, findings=tuple(lint(commit)))
            for index, commit in enumerate(self.commits, start=1)
        )
        self.findings = [finding for entry in self.entries for finding in entry.findings]

    def count(self, severity: str) -> int:
        return sum(1 for finding in self.findings if finding.severity == severity)

    @property
    def score(self) -> int:
        penalty = sum(PENALTY[finding.severity] for finding in self.findings)
        return max(0, 100 - penalty)

    @property
    def status(self) -> str:
        if self.count("error"):
            return "fail"
        if self.count("warning") or self.count("note"):
            return "warn"
        return "pass"

    @property
    def exit_code(self) -> int:
        return 1 if self.status == "fail" else 0

    def filtered(self, min_severity: str = "note") -> CommitLintReport:
        limit = SEVERITY_ORDER[min_severity]
        report = CommitLintReport(commits=self.commits, source=self.source)
        report.entries = tuple(
            Entry(
                index=entry.index,
                commit=entry.commit,
                findings=tuple(f for f in entry.findings if SEVERITY_ORDER[f.severity] <= limit),
            )
            for entry in self.entries
        )
        report.findings = [finding for entry in report.entries for finding in entry.findings]
        return report

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "commits": len(self.commits),
            "errors": self.count("error"),
            "warnings": self.count("warning"),
            "notes": self.count("note"),
            "score": self.score,
            "status": self.status,
            "entries": [
                {
                    "index": entry.index,
                    "header": entry.label,
                    "type": entry.commit.type,
                    "scope": entry.commit.scope,
                    "findings": [finding.as_dict() for finding in entry.findings],
                }
                for entry in self.entries
            ],
        }

    def render(self) -> str:
        broken = [entry for entry in self.entries if entry.findings]
        lines = [
            f"{self.source}  -  {len(self.commits)} commit(s), {len(broken)} with findings",
            f"{self.count('error')} error(s), {self.count('warning')} warning(s), "
            f"{self.count('note')} note(s)  -  score {self.score}/100  -  {self.status.upper()}",
        ]
        for entry in broken:
            lines.append("")
            lines.append(f"#{entry.index}  {entry.label}")
            for finding in entry.findings:
                lines.append(f"    {finding.severity:<7} {finding.rule:<24} {finding.message}")
        if not broken:
            lines += ["", "Every message follows the convention."]
        return "\n".join(lines)
