# nldate

Python package (`src/nldate/`, managed with uv) exposing `parse(s: str, today: date | None = None) -> date`, which converts natural-language dates ("5 days before December 1st, 2025", "1 year and 2 months after yesterday", "next Tuesday") into `datetime.date`.

## Rules
- The tests in `tests/` are the spec. Do not edit or weaken them to make them pass. If a test looks wrong, stop and tell me.
- Unrecognized input (including the empty string) must raise `ValueError`.
- `today` defaults to `date.today()`; always use it as the reference for relative expressions.
- Standard library only. No dateparser, dateutil, or other parsing libs.
- Fully type-annotated code, and no `# type: ignore` or ruff `noqa` unless unavoidable.

## Before finishing, all of these must pass
- `uv run pytest`
- `uv run mypy src/`
- `uv run ruff check`
- `uv run ruff format --check` (run `uv run ruff format` to fix)

## Conventions
- `next <weekday>` / `last <weekday>` are strictly after / before today (same weekday = 7 days away).
- Month/year arithmetic clamps to the last valid day (Jan 31 + 1 month = Feb 28).
- `12/1/2025` is US-style (month first).
