# -*- coding: utf-8 -*-
import re
import logging
from utils import clean_number, normalize_date, clean_name

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Invoice header meta (for the "Invoice Info" sheet — supplementary only)
# ---------------------------------------------------------------------------
_HEADER_PATTERNS: dict[str, list[str]] = {
    "invoice_number": [
        r"Invoice\s*(?:No\.?|Number|Num\.?|#)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-/]{2,30})",
        r"Bill\s*(?:No\.?|Number)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-/]{2,30})",
        r"Inv\.?\s*(?:No\.?|#)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-/]{2,30})",
        r"Tax\s*Invoice\s*(?:No\.?|#)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-/]{2,30})",
    ],
    "invoice_date": [
        r"Invoice\s*Date\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"Invoice\s*Date\s*[:\-]?\s*(\d{1,2}\s+\w+\s+\d{4})",
        r"Dated?\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"Date\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
    ],
    "customer_name": [
        r"Bill(?:ed)?\s*To\s*[:\-]?\s*\n?\s*([A-Za-z][A-Za-z0-9\s\.,&'\-]{2,60}?)(?:\n|GSTIN|GST|$)",
        r"Customer\s*(?:Name)?\s*[:\-]?\s*\n?\s*([A-Za-z][A-Za-z0-9\s\.,&'\-]{2,60}?)(?:\n|$)",
    ],
    "vendor_name": [
        r"(?:From|Vendor|Seller|Billed\s*(?:From|By))\s*[:\-]?\s*\n?\s*([A-Za-z][A-Za-z0-9\s\.,&'\-]{2,60}?)(?:\n|GSTIN|GST|$)",
    ],
    "po_number": [
        r"P\.?O\.?\s*(?:No\.?|Number|#)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-/]{1,20})",
        r"Purchase\s*Order\s*(?:No\.?|#)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-/]{1,20})",
    ],
    "total_amount": [
        r"(?:Grand\s+Total|Total\s+Amount\s+Due|Net\s+Payable|Amount\s+Due)\s*[:\-]?\s*(?:INR|Rs\.?|₹|USD|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
        r"Total\s+Amount\s*[:\-]?\s*(?:INR|Rs\.?|₹|USD|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
    ],
}

_META_PROCESSORS = {
    "invoice_date":  normalize_date,
    "customer_name": clean_name,
    "vendor_name":   clean_name,
    "total_amount":  clean_number,
    "invoice_number": str.strip,
    "po_number":      str.strip,
}

_META_LABELS = {
    "invoice_number": "Invoice Number",
    "invoice_date":   "Invoice Date",
    "customer_name":  "Customer Name",
    "vendor_name":    "Vendor Name",
    "po_number":      "PO Number",
    "total_amount":   "Total Amount",
}


def extract_invoice_meta(text: str) -> dict[str, str]:
    """Extract header-level fields from invoice text (for info sheet)."""
    meta: dict[str, str] = {}
    for key, patterns in _HEADER_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                raw  = m.group(1).strip()
                proc = _META_PROCESSORS.get(key, str.strip)
                meta[_META_LABELS[key]] = proc(raw)
                break
    return meta


# ---------------------------------------------------------------------------
# Raw table extraction  — no column mapping, grab as-is
# ---------------------------------------------------------------------------

def _clean_cell(v) -> str:
    """Normalise a pdfplumber cell to a clean string."""
    if v is None:
        return ""
    s = str(v)
    # Merge mid-word line breaks (e.g. "Treat\nment" → "Treatment")
    s = re.sub(r"([a-z])\n([a-z])", r"\1\2", s)
    s = s.replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def _score_table(data: list[list]) -> int:
    """Score a table by count of non-empty cells."""
    return sum(1 for row in data for cell in row if _clean_cell(cell))


def _merge_continuation_tables(tables: list[dict]) -> list[list[list]]:
    """
    Merge tables across pages that appear to be the same table continued.
    Two tables are merged when the second has the same column count as the first
    AND its first row looks like a data row (not a new header).
    Returns a list of merged table data (list of rows).
    """
    if not tables:
        return []

    # Convert to cleaned data
    cleaned_tables: list[list[list[str]]] = []
    for tbl in tables:
        rows = [[_clean_cell(c) for c in row] for row in tbl["data"]]
        rows = [r for r in rows if any(r)]   # drop blank rows
        if rows:
            cleaned_tables.append(rows)

    if not cleaned_tables:
        return []

    merged: list[list[list[str]]] = [cleaned_tables[0]]

    for tbl in cleaned_tables[1:]:
        prev = merged[-1]
        prev_ncols = len(prev[0]) if prev else 0
        curr_ncols = len(tbl[0])  if tbl  else 0

        if prev_ncols == curr_ncols:
            # Likely continuation — append rows (skip repeated header if identical)
            if tbl[0] == prev[0]:
                merged[-1].extend(tbl[1:])
            else:
                merged[-1].extend(tbl)
        else:
            merged.append(tbl)

    return merged


# Keywords whose presence in a row strongly suggests it is a column-header row.
# We score every row and pick the one with the most hits.
_HEADER_ROW_KEYWORDS = [
    "sl", "sl.", "sl no", "si no", "s.no", "sno", "sr", "sr no", "serial",
    "hsn", "sac", "hsn/sac", "hsn no",
    "description", "material", "particulars",
    "qty", "quantity",
    "rate", "amount", "total value", "total",
    "uom", "unit",
    "width", "length", "thickness", "core", "treatment", "packing",
]


def _header_row_score(row: list[str]) -> int:
    """Return how many cells in a row match known header keywords."""
    score = 0
    for cell in row:
        cell_low = cell.lower()
        for kw in _HEADER_ROW_KEYWORDS:
            # Whole-word / phrase match to avoid false positives
            if re.search(r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])", cell_low):
                score += 1
                break        # count each cell only once
    return score


def _find_header_row_idx(table: list[list[str]]) -> int:
    """
    Scan all rows and return the index of the one most likely to be the
    line-item column header row.  Falls back to 0 if nothing scores >= 2.
    """
    best_idx, best_score = 0, 0
    for idx, row in enumerate(table):
        s = _header_row_score(row)
        if s > best_score:
            best_score = s
            best_idx   = idx
    return best_idx if best_score >= 2 else 0


def extract_best_table(tables: list[dict]) -> dict:
    """
    Find and return the line-item table from the PDF.

    Strategy
    --------
    Many Indian invoices wrap the ENTIRE page in one big pdfplumber table
    (company info, addresses, line items, terms — all in one grid).
    We handle this by scanning every row to find the one that looks most
    like a column-header row (SI No, HSN No, Description, Qty, Rate …),
    then slicing from that point.

    Returns:
        found    (bool)
        headers  (list[str])   — the detected header row, as-is from PDF
        rows     (list[list[str]])  — data rows below the header
        n_cols   (int)
    """
    if not tables:
        return {"found": False, "headers": [], "rows": [], "n_cols": 0}

    merged_tables = _merge_continuation_tables(tables)

    # Pick the table with the highest content score (most non-empty cells)
    best: list[list[str]] = max(merged_tables, key=lambda t: _score_table(t))

    if not best:
        return {"found": False, "headers": [], "rows": [], "n_cols": 0}

    # Find the actual column-header row (may not be row 0 in full-page tables)
    header_idx = _find_header_row_idx(best)
    raw_headers = best[header_idx]

    # Width = max columns across all rows from header onward
    relevant = best[header_idx:]
    n_cols   = max(len(row) for row in relevant)

    # Build clean header labels; blank header cells become "Col<n>"
    headers = [
        (raw_headers[i].strip() if i < len(raw_headers) and raw_headers[i].strip()
         else f"Col{i+1}")
        for i in range(n_cols)
    ]

    # Pad/trim data rows — filter out non-tabular content
    data_rows = []
    for row in best[header_idx + 1:]:
        padded = (row + [""] * (n_cols - len(row)))[:n_cols]
        non_empty = [c for c in padded if c.strip()]

        # Completely empty row → skip
        if not non_empty:
            continue

        first_cell = padded[0].strip()

        # Long paragraph in first cell (>80 chars) → terms/notes/summary text, skip
        if len(first_cell) > 80:
            continue

        # Only 1 non-empty cell → a label/heading outside the table, skip
        if len(non_empty) < 2:
            continue

        data_rows.append(padded)

    if not data_rows:
        return {"found": False, "headers": [], "rows": [], "n_cols": 0}

    return {
        "found":   True,
        "headers": headers,
        "rows":    data_rows,
        "n_cols":  n_cols,
    }
