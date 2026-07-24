"""Mesoamerican calendar conversion compatible with the UtahGeology demo.

The public UI uses the GMT 584283 correlation. Internally the original page
stores the civil-day anchor as 584282.5, then rounds like JavaScript.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
import math


CORRELATION = 584282.5
CORRELATION_LABEL = "GMT 584283"

MAYA_TZOLKIN = [
    "Imix'", "Ik'", "Ak'b'al", "K'an", "Chikchan", "Kimi", "Manik'",
    "Lamat", "Muluk", "Ok", "Chuwen", "Eb'", "B'en", "Ix", "Men",
    "K'ib'", "Kab'an", "Etz'nab'", "Kawak", "Ajaw",
]

AZTEC_SIGNS = [
    "Cipactli", "Ehecatl", "Calli", "Cuetzpalin", "Coatl", "Miquiztli",
    "Mazatl", "Tochtli", "Atl", "Itzcuintli", "Ozomahtli", "Malinalli",
    "Acatl", "Ocelotl", "Cuauhtli", "Cozcacuauhtli", "Ollin", "Tecpatl",
    "Quiahuitl", "Xochitl",
]

HAAB_MONTHS = [
    "Pop", "Wo'", "Sip", "Sotz'", "Sek", "Xul", "Yaxk'in", "Mol",
    "Ch'en", "Yax", "Sak'", "Keh", "Mak", "K'ank'in", "Muwan", "Pax",
    "K'ayab", "Kumk'u", "Wayeb'",
]


def js_round(value: float) -> int:
    """Match JavaScript Math.round for the positive values used here."""
    return math.floor(value + 0.5)


def gregorian_to_jdn(value: date) -> int:
    """Return the civil-day JDN convention used by the reference page."""
    m, d, y = value.month, value.day, value.year
    a = math.floor((14 - m) / 12)
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return (
        math.floor((153 * m2 + 2) / 5)
        + 365 * y2
        + math.floor(y2 / 4)
        - math.floor(y2 / 100)
        + math.floor(y2 / 400)
        + (d - 1)
        - 32045
    )


def long_count_array(total_days: int) -> list[int]:
    values = [0, 0, 0, 0, 0]
    remainder = total_days
    for idx, unit in enumerate((144000, 7200, 360, 20)):
        values[idx] = remainder // unit
        remainder %= unit
    values[4] = remainder
    return values


@dataclass(frozen=True)
class CalendarResult:
    birth_date: str
    jdn: int
    total_days: int
    long_count: list[int]
    long_count_text: str
    tzolkin_number: int
    tzolkin_maya_name: str
    symbol_index: int
    aztec_name: str
    haab_day: int
    haab_month_index: int
    haab_month: str
    night_lord: int
    product_no: int
    correlation: str

    def to_dict(self) -> dict:
        return asdict(self)


def convert_birth_date(value: date) -> CalendarResult:
    jdn = gregorian_to_jdn(value)
    total_days = js_round(jdn - CORRELATION)
    lc = long_count_array(total_days)

    tzolkin_number = ((total_days + 3) % 13) + 1
    symbol_index = (total_days + 19) % 20

    day_of_haab = (total_days - 17) % 365
    haab_day = day_of_haab % 20
    haab_month_index = day_of_haab // 20

    night_lord = ((20 * lc[3] + lc[4] + 8) % 9) + 1
    product_no = ((symbol_index + 4) % 20) + 1

    return CalendarResult(
        birth_date=value.isoformat(),
        jdn=jdn,
        total_days=total_days,
        long_count=lc,
        long_count_text=".".join(str(n) for n in lc),
        tzolkin_number=tzolkin_number,
        tzolkin_maya_name=MAYA_TZOLKIN[symbol_index],
        symbol_index=symbol_index,
        aztec_name=AZTEC_SIGNS[symbol_index],
        haab_day=haab_day,
        haab_month_index=haab_month_index,
        haab_month=HAAB_MONTHS[haab_month_index],
        night_lord=night_lord,
        product_no=product_no,
        correlation=CORRELATION_LABEL,
    )

