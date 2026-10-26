from __future__ import annotations

from pathlib import Path

from commit_message_linter.changelog import build_changelog
from commit_message_linter.messages import parse_commits
from commit_message_linter.report import CommitLintReport

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_changelog_groups_by_type() -> None:
    commits = parse_commits((EXAMPLES / "clean-commits.txt").read_text(encoding="utf-8"))
    text = build_changelog(commits, version="v1.2.0", date="2026-01-05")
    assert "## v1.2.0 - 2026-01-05" in text
    assert "### Breaking changes" in text
    assert text.index("### Features") < text.index("### Fixes")
    assert "- **api**: add idempotency keys" in text
    assert "**BREAKING**" in text


def test_changelog_ignores_unconventional_messages() -> None:
    text = build_changelog(parse_commits("Update the readme\n---\nfeat: add api\n"))
    assert "Update the readme" not in text
    assert "add api" in text


def test_changelog_without_commits() -> None:
    assert "No conventional commits found." in build_changelog([])


def test_report_scores_clean_commits() -> None:
    commits = parse_commits((EXAMPLES / "clean-commits.txt").read_text(encoding="utf-8"))
    report = CommitLintReport(commits=commits, source="clean")
    assert report.score == 100
    assert report.status == "pass"
    assert report.exit_code == 0
    assert "Every message follows the convention." in report.render()


def test_report_flags_bad_commits() -> None:
    commits = parse_commits((EXAMPLES / "commits.txt").read_text(encoding="utf-8"))
    report = CommitLintReport(commits=commits, source="commits.txt")
    assert report.status == "fail"
    assert report.exit_code == 1
    assert report.count("error") >= 1
    assert report.count("warning") >= 3
    assert report.score < 100
    assert "#3" in report.render()


def test_report_json_shape() -> None:
    commits = parse_commits("feat(api): add\n---\nunknown: nope\n")
    payload = CommitLintReport(commits=commits, source="x").as_dict()
    assert payload["commits"] == 2
    assert payload["errors"] >= 1
    assert payload["entries"][0]["type"] == "feat"
    assert payload["status"] == "fail"


def test_filtering_by_severity_keeps_errors_only() -> None:
    commits = parse_commits((EXAMPLES / "commits.txt").read_text(encoding="utf-8"))
    report = CommitLintReport(commits=commits, source="commits.txt").filtered("error")
    assert {finding.severity for finding in report.findings} == {"error"}
    assert report.count("warning") == 0


def test_filtering_does_not_mutate_the_original() -> None:
    report = CommitLintReport(commits=parse_commits("Feat: nope\n"), source="x")
    before = len(report.findings)
    report.filtered("error")
    assert len(report.findings) == before
