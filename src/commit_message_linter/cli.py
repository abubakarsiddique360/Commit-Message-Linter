"""Command line entry point: lint, message, changelog, rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from commit_message_linter.changelog import build_changelog
from commit_message_linter.messages import parse_commits, parse_message
from commit_message_linter.report import CommitLintReport
from commit_message_linter.rules import RULES, SEVERITIES


class InputError(ValueError):
    pass


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc.strerror or exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="commit-lint",
        description="Lint conventional commit messages from a file or the command line.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    lint_cmd = sub.add_parser("lint", help="lint every commit in a batch file")
    lint_cmd.add_argument("file", help="file with commits separated by a line of '---'")
    lint_cmd.add_argument("--json", action="store_true")
    lint_cmd.add_argument("--min-severity", choices=SEVERITIES, default="note")

    message_cmd = sub.add_parser("message", help="lint a single message given on the command line")
    message_cmd.add_argument("text", help="the commit message; use \\n for line breaks")

    changelog_cmd = sub.add_parser("changelog", help="build a markdown changelog")
    changelog_cmd.add_argument("file")
    changelog_cmd.add_argument("--version", default="Unreleased")
    changelog_cmd.add_argument("--date", default="")

    sub.add_parser("rules", help="list every rule")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "rules":
        for rule in RULES:
            print(f"{rule.id:<24}{rule.severity:<9}{rule.summary}")
        return 0

    if args.command == "message":
        text = args.text.replace("\\n", "\n")
        report = CommitLintReport(commits=[parse_message(text)], source="message")
    else:
        try:
            text = _read(args.file)
        except InputError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        commits = parse_commits(text)
        if not commits:
            print("error: no commits found in the file", file=sys.stderr)
            return 2
        if args.command == "changelog":
            print(build_changelog(commits, version=args.version, date=args.date))
            return 0
        report = CommitLintReport(commits=commits, source=Path(args.file).name).filtered(args.min_severity)

    if args.command == "message":
        print(report.render())
        return report.exit_code

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(report.render())
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
