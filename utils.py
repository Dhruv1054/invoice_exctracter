import re
from datetime import datetime

DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
    "%m/%d/%Y", "%m-%d-%Y",
    "%d %B %Y", "%d %b %Y",
    "%B %d, %Y", "%b %d, %Y",
    "%Y-%m-%d", "%Y/%m/%d",
]


def clean_number(value: str) -> str:
    """Remove commas, currency symbols, and return clean float string."""
    if not value:
        return ""
    cleaned = re.sub(r"[,\s₹$]", "", value).strip()
    try:
        return str(float(cleaned))
    except ValueError:
        return cleaned


def normalize_date(value: str) -> str:
    """Parse various date formats and normalize to DD/MM/YYYY."""
    if not value:
        return ""
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return value


def clean_name(value: str) -> str:
    """Strip extra whitespace and newlines from extracted names."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()
