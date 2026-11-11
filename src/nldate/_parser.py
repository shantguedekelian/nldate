"""Natural-language date parsing (standard library only)."""

import calendar
import re
from datetime import date, timedelta

_MONTHS: dict[str, int] = {}
for _i, _name in enumerate(calendar.month_name):
    if _name:
        _MONTHS[_name.lower()] = _i
        _MONTHS[calendar.month_abbr[_i].lower()] = _i
_MONTHS["sept"] = 9

_WEEKDAYS: dict[str, int] = {}
for _i, _name in enumerate(calendar.day_name):
    _WEEKDAYS[_name.lower()] = _i
    _WEEKDAYS[calendar.day_abbr[_i].lower()] = _i
_WEEKDAYS.update({"tues": 1, "weds": 2, "thur": 3, "thurs": 3})

_NUMBER_WORDS: dict[str, int] = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}

_MONTH_RE = "|".join(sorted(_MONTHS, key=len, reverse=True))
_WEEKDAY_RE = "|".join(sorted(_WEEKDAYS, key=len, reverse=True))
_NUM_RE = r"\d+|" + "|".join(_NUMBER_WORDS)
_QUANTITY_RE = rf"(?:{_NUM_RE})\s+(?:day|week|month|year)s?"
_OFFSET_RE = rf"{_QUANTITY_RE}(?:\s*(?:,\s*and|,|and)?\s*{_QUANTITY_RE})*"

_QUANTITY = re.compile(rf"({_NUM_RE})\s+(day|week|month|year)s?")
_OFFSET = re.compile(_OFFSET_RE)
_ANCHORED = re.compile(r"(.+?)\s+(?:before|after|from|past)\s+(.+)")
_IN = re.compile(r"in\s+(.+)")
_AGO = re.compile(r"(.+?)\s+ago")
_ISO = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
_YMD_SLASH = re.compile(r"(\d{4})/(\d{1,2})/(\d{1,2})")
_US = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_SUFFIX = r"(?:st|nd|rd|th)?"
_MONTH_FIRST = re.compile(
    rf"({_MONTH_RE})\.?\s+(\d{{1,2}}){_SUFFIX}(?:\s*,?\s*(\d{{4}}))?"
)
_DAY_FIRST = re.compile(
    rf"(?:the\s+)?(\d{{1,2}}){_SUFFIX}\s+(?:of\s+)?({_MONTH_RE})\.?(?:\s*,?\s*(\d{{4}}))?"
)
_WEEKDAY_REF = re.compile(rf"(next|last|previous)\s+({_WEEKDAY_RE})")
_PERIOD_REF = re.compile(r"(next|last|previous)\s+(week|month|year)")


def parse(s: str, today: date | None = None) -> date:
    """Convert a natural-language date expression into a ``date``.

    Raises ``ValueError`` for unrecognized or invalid input.
    """
    if today is None:
        today = date.today()
    text = re.sub(r"\s+", " ", s.strip().lower())
    if not text:
        raise ValueError("empty date expression")
    try:
        return _parse_expr(text, today)
    except OverflowError as exc:
        raise ValueError(f"date out of range: {s!r}") from exc


def _parse_expr(text: str, today: date) -> date:
    if m := _ANCHORED.fullmatch(text):
        offset_text, anchor_text = m.groups()
        years, months, days = _parse_offset(offset_text)
        anchor = _parse_expr(anchor_text, today)
        # The keyword between the offset and the anchor decides the direction.
        keyword = text[m.end(1) : m.start(2)].strip()
        sign = -1 if keyword == "before" else 1
        return _shift(anchor, sign * years, sign * months, sign * days)
    if m := _IN.fullmatch(text):
        years, months, days = _parse_offset(m.group(1))
        return _shift(today, years, months, days)
    if m := _AGO.fullmatch(text):
        years, months, days = _parse_offset(m.group(1))
        return _shift(today, -years, -months, -days)
    return _parse_base(text, today)


def _parse_offset(text: str) -> tuple[int, int, int]:
    """Return (years, months, days) for an offset such as '1 year and 2 months'."""
    if not _OFFSET.fullmatch(text):
        raise ValueError(f"unrecognized offset: {text!r}")
    years = months = days = 0
    for num, unit in _QUANTITY.findall(text):
        n = int(num) if num.isdigit() else _NUMBER_WORDS[num]
        if unit == "year":
            years += n
        elif unit == "month":
            months += n
        elif unit == "week":
            days += 7 * n
        else:
            days += n
    return years, months, days


def _shift(anchor: date, years: int, months: int, days: int) -> date:
    total = anchor.year * 12 + (anchor.month - 1) + years * 12 + months
    year, month = divmod(total, 12)
    month += 1
    if not 1 <= year <= 9999:
        raise ValueError("date out of range")
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day) + timedelta(days=days)


def _parse_base(text: str, today: date) -> date:
    if text in ("today", "now"):
        return today
    if text == "tomorrow":
        return today + timedelta(days=1)
    if text == "yesterday":
        return today - timedelta(days=1)
    if m := _WEEKDAY_REF.fullmatch(text):
        target = _WEEKDAYS[m.group(2)]
        if m.group(1) == "next":
            return today + timedelta(days=(target - today.weekday()) % 7 or 7)
        return today - timedelta(days=(today.weekday() - target) % 7 or 7)
    if m := _PERIOD_REF.fullmatch(text):
        sign = 1 if m.group(1) == "next" else -1
        unit = m.group(2)
        if unit == "week":
            return today + timedelta(days=7 * sign)
        if unit == "month":
            return _shift(today, 0, sign, 0)
        return _shift(today, sign, 0, 0)
    return _parse_absolute(text, today)


def _make_date(year: int, month: int, day: int) -> date:
    return date(year, month, day)  # raises ValueError if invalid


def _parse_absolute(text: str, today: date) -> date:
    if m := _ISO.fullmatch(text) or _YMD_SLASH.fullmatch(text):
        return _make_date(int(m[1]), int(m[2]), int(m[3]))
    if m := _US.fullmatch(text):
        return _make_date(int(m[3]), int(m[1]), int(m[2]))
    if m := _MONTH_FIRST.fullmatch(text):
        year = int(m[3]) if m[3] else today.year
        return _make_date(year, _MONTHS[m[1]], int(m[2]))
    if m := _DAY_FIRST.fullmatch(text):
        year = int(m[3]) if m[3] else today.year
        return _make_date(year, _MONTHS[m[2]], int(m[1]))
    raise ValueError(f"unrecognized date expression: {text!r}")
