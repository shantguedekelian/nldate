from datetime import date

import pytest

from nldate import parse

# Wednesday
TODAY = date(2025, 11, 12)


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("December 1st, 2025", date(2025, 12, 1)),
        ("December 1, 2025", date(2025, 12, 1)),
        ("1 December 2025", date(2025, 12, 1)),
        ("2025-12-01", date(2025, 12, 1)),
        ("12/1/2025", date(2025, 12, 1)),
        ("february 29th, 2024", date(2024, 2, 29)),
    ],
)
def test_absolute_dates(s: str, expected: date) -> None:
    assert parse(s, today=TODAY) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("today", date(2025, 11, 12)),
        ("tomorrow", date(2025, 11, 13)),
        ("yesterday", date(2025, 11, 11)),
    ],
)
def test_keywords(s: str, expected: date) -> None:
    assert parse(s, today=TODAY) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("in 3 days", date(2025, 11, 15)),
        ("3 days ago", date(2025, 11, 9)),
        ("in 2 weeks", date(2025, 11, 26)),
        ("in 1 month", date(2025, 12, 12)),
        ("1 year ago", date(2024, 11, 12)),
    ],
)
def test_offsets_from_today(s: str, expected: date) -> None:
    assert parse(s, today=TODAY) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("5 days before December 1st, 2025", date(2025, 11, 26)),
        ("2 weeks after December 1st, 2025", date(2025, 12, 15)),
        ("1 day after tomorrow", date(2025, 11, 14)),
        ("1 year and 2 months after yesterday", date(2027, 1, 11)),
    ],
)
def test_offsets_from_anchor(s: str, expected: date) -> None:
    assert parse(s, today=TODAY) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("next Tuesday", date(2025, 11, 18)),
        ("last Friday", date(2025, 11, 7)),
        ("next Wednesday", date(2025, 11, 19)),
        ("last Wednesday", date(2025, 11, 5)),
        ("next monday", date(2025, 11, 17)),
    ],
)
def test_weekdays(s: str, expected: date) -> None:
    assert parse(s, today=TODAY) == expected


def test_month_end_rollover_clamps() -> None:
    assert parse("1 month after January 31st, 2025", today=TODAY) == date(2025, 2, 28)


def test_leap_day_arithmetic() -> None:
    assert parse("1 day after February 28th, 2024", today=TODAY) == date(2024, 2, 29)
    assert parse("1 year after February 29th, 2024", today=TODAY) == date(2025, 2, 28)


def test_default_today_is_used() -> None:
    assert parse("today") == date.today()


@pytest.mark.parametrize(
    "s",
    [
        "",
        "   ",
        "asdf",
        "February 30th, 2025",
        "5 days before",
        "next Funday",
    ],
)
def test_invalid_input_raises(s: str) -> None:
    with pytest.raises(ValueError):
        parse(s, today=TODAY)


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("the day after tomorrow", date(2025, 11, 14)),
        ("the day before yesterday", date(2025, 11, 10)),
        ("the day after December 1st, 2025", date(2025, 12, 2)),
        ("the day before December 1st, 2025", date(2025, 11, 30)),
        ("the day after next Tuesday", date(2025, 11, 19)),
        ("a week after tomorrow", date(2025, 11, 20)),
        ("a week from tomorrow", date(2025, 11, 20)),
        ("a day ago", date(2025, 11, 11)),
        ("in a week", date(2025, 11, 19)),
        ("three days ago", date(2025, 11, 9)),
        ("two weeks from today", date(2025, 11, 26)),
    ],
)
def test_article_and_word_forms(s: str, expected: date) -> None:
    assert parse(s, today=TODAY) == expected
