from __future__ import annotations

import math
import re
import unicodedata
from datetime import date, datetime
from typing import Any


def norm_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if isinstance(value, float) and math.isnan(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def norm_key(value: Any) -> str:
    text = norm_text(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None or norm_text(value) == "":
        return default
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:
            return default
    s = norm_text(value).replace("R$", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return default


def to_iso_date(value: Any) -> str:
    if value is None or norm_text(value) == "":
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    s = norm_text(value)
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d/%m.%y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(s[:10], fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return s[:10]


def moeda(value: Any) -> str:
    try:
        return f"R$ {float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def hoje() -> str:
    return date.today().strftime("%Y-%m-%d")
