"""Turn conventional commits into a grouped changelog."""

from __future__ import annotations

from commit_message_linter.messages import CommitMessage

SECTION_TITLES = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Performance",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "test": "Tests",
    "build": "Build",
    "ci": "Continuous integration",
    "style": "Style",
    "chore": "Chores",
    "revert": "Reverts",
}
SECTION_ORDER = tuple(SECTION_TITLES)


def _entry(message: CommitMessage) -> str:
    scope = f"**{message.scope}**: " if message.scope else ""
    breaking = " **BREAKING**" if message.breaking else ""
    return f"- {scope}{message.subject}{breaking}"


def build_changelog(commits: list[CommitMessage], version: str = "Unreleased", date: str = "") -> str:
    """Group commits by type, breaking changes first. Unconventional messages are ignored."""
    usable = [commit for commit in commits if commit.matched and commit.subject]
    heading = f"## {version}" + (f" - {date}" if date else "")
    lines = [heading]

    breaking = [commit for commit in usable if commit.breaking]
    if breaking:
        lines += ["", "### Breaking changes"]
        lines += [_entry(commit) for commit in breaking]

    for commit_type in SECTION_ORDER:
        group = [commit for commit in usable if commit.type.lower() == commit_type]
        if not group:
            continue
        lines += ["", f"### {SECTION_TITLES[commit_type]}"]
        lines += [_entry(commit) for commit in group]

    if len(lines) == 1:
        lines += ["", "No conventional commits found."]
    return "\n".join(lines)
