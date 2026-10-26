# Commit-Message-Linter

[![CI](https://github.com/abubakarsiddique360/Commit-Message-Linter/actions/workflows/ci.yml/badge.svg)](https://github.com/abubakarsiddique360/Commit-Message-Linter/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%20%7C%203.12-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![dependencies](https://img.shields.io/badge/dependencies-none-success)

Read [Conventional Commits](https://www.conventionalcommits.org/) the way a reviewer does:
check the header, the body and the footers, score a whole batch of messages, and turn the
conventional ones into a grouped changelog. Standard library only.

## Why it exists

A commit log is documentation nobody proofreads. A single `Update stuff` breaks the story, and a
`feat!:` without a `BREAKING CHANGE:` footer hides a migration from everyone who upgrades.
Generic commit hooks stop at the header. This tool checks the parts people actually read weeks
later, and it can also generate the changelog from the same rules, so the convention pays for
itself twice.

## Install

```bash
pip install -e .
```

Python 3.10+, no runtime dependencies.

## Usage

```bash
# lint every commit in a batch file
commit-lint lint examples/commits.txt

# machine readable output
commit-lint lint examples/commits.txt --json

# only report errors, ignore warnings and notes
commit-lint lint examples/commits.txt --min-severity error

# check the message you are about to type
commit-lint message "feat(parser): add retry with backoff"

# build a changelog section from the same commits
commit-lint changelog examples/clean-commits.txt --version v1.2.0 --date 2026-01-05

# explain every rule
commit-lint rules
```

Exit codes: `0` the batch passes, `1` an error was found, `2` the input cannot be read.
A single commit as a hook is just `commit-lint message "$(cat .git/COMMIT_EDITMSG)"`.

### Batch file format

Commits are separated by a line containing only `---`, which keeps the file readable in an
editor and trivial to generate:

```text
feat(parser): add retry with backoff

Retries transient timeouts up to three times before failing.

Refs: #412
---
fix: handle empty CSV header
```

## Rules

| Rule | Severity | What it catches |
| --- | --- | --- |
| `empty-message` | error | The message has no content at all. |
| `header-format` | error | Header is not `type(scope): subject`. |
| `unknown-type` | error | Type is not one of the eleven conventional types. |
| `subject-empty` | error | `feat:` with nothing after the colon. |
| `scope-empty` | error | `feat():` with an empty scope. |
| `type-case` | warning | `Feat:` instead of `feat:`. |
| `scope-format` | warning | Scope is not lowercase words joined by `-`. |
| `header-too-long` | warning | Header over 72 characters, truncated by `git log --oneline`. |
| `subject-trailing-period` | warning | Subject reads like a sentence. |
| `subject-capitalised` | warning | Subject starts with a capital, so it is not imperative. |
| `attached-body` | warning | Body glued to the header without a blank line. |
| `body-line-too-long` | warning | Body line over 100 characters. |
| `breaking-note-missing` | warning | `!` without a `BREAKING CHANGE:` footer explaining the migration. |
| `footer-token-case` | note | Footer token is not lowercase with hyphens. |
| `revert-reference` | warning | A revert that does not point at the commit it undoes. |

Score: 100 minus 25 per error, 6 per warning and 2 per note, floored at zero. The status is
`fail` when there is an error, `warn` when there is a warning or note, `pass` otherwise.

## Example output

```text
commits.txt  -  8 commit(s), 6 with findings
1 error(s), 6 warning(s), 2 note(s)  -  score 35/100  -  FAIL

#3  unknown: rework the whole importer
    error   unknown-type             type 'unknown' is not one of feat, fix, docs, ...

#4  Feat(Api): Add The New Endpoint.
    warning type-case                type 'Feat' should be lowercase
    warning scope-format             scope 'Api' should be lowercase words joined by '-'
    warning subject-trailing-period  the subject should not end with a period
```

## Changelog output

```bash
commit-lint changelog examples/clean-commits.txt --version v1.2.0
```

```markdown
## v1.2.0

### Breaking changes
- **api**: remove the legacy endpoint **BREAKING**

### Features
- **api**: add idempotency keys

### Fixes
- **cache**: stop returning stale entries
```

Sections are ordered `feat`, `fix`, `perf`, `refactor`, `docs`, ... and empty sections are
omitted. Messages that do not follow the convention are skipped instead of polluting the notes.

## Design notes

- **Parsing is layered.** `messages.py` turns raw text into header, body and footers; `rules.py`
  never touches strings from the file system, it only inspects the parsed object.
- **Footers are a trailing paragraph** whose every line matches `Token: value` or `Token #123`.
  That matches the spec closely enough to keep `Signed-off-by:` and `Refs:` trailers out of the body.
- **Rules are data**, so `commit-lint rules` is generated from the same catalogue that produces
  findings and the two can never drift.
- **Batches are first class.** Reviewing a PR's commits one hook at a time is noisy; the report
  gives one score for the whole batch and per-commit detail.
- **No git dependency.** It reads text, so it also works on exported logs, changelog drafts and
  tests.

## Project layout

```text
src/commit_message_linter/
  messages.py   header/body/footer parsing and batch splitting
  rules.py      the 15-rule catalogue and lint()
  changelog.py  grouped markdown changelog from conventional commits
  report.py     per-commit entries, scoring, status, text and JSON rendering
  cli.py        lint / message / changelog / rules
examples/
  commits.txt        a batch that breaks most rules
  clean-commits.txt  a batch that passes
tests/               58 tests across parsing, rules, report and CLI
```

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

CI runs the suite on Python 3.10 and 3.12, checks formatting, then lints both example batches and
prints a changelog so the documented output cannot silently change.

## Limitations

- Only the header grammar is enforced strictly; the body is checked for length and spacing, not
  for content quality.
- `.gitmessage` templates and multi-line squash bodies are supported, but merge commits such as
  `Merge branch 'x'` are reported as `header-format` errors, which is intended.
- The changelog groups by type but does not link commits or issues.
- Messages are assumed to be UTF-8.

## License

MIT, copyright (c) 2026 ABU BAKAR SIDDIQUE.
