"""
sif_convert.py  -  Core logic for parsing geological assay-lab certificate
SIF files (Standard Interchange Format) into tidy tabular data.

These are the readable text "certificate" files that assay labs (ALS, SGS,
Bureau Veritas, Intertek, etc.) send for import into Micromine / Geobank.
They usually carry a multi-row header block describing each analyte column,
followed by the sample rows:

    ...preamble / method table (ignored)...
    ,,,Au ,Cu ,Ag            <- analyte / element names
    ,,,ppm,% ,ppm            <- units
    ,,,Au-AA23,ME-ICP61,...  <- lab method codes
    ,,,0.01,0.01,0.2         <- lower detection limits
    SAMPLE,DESCRIPTION,Au,Cu,Ag   <- (sometimes) a column-label row
    SMP0001,,1.23,0.45,2.1        <- data rows
    SMP0002,,<0.01,0.30,1.8       <- "<x" = below detection limit

This module is pure standard library and works entirely in memory (no file
reads/writes), so it is safe to import in the Streamlit Cloud environment.
The command-line wrapper lives in the standalone sif-to-csv repo; here we
expose parse_text() plus helpers that return CSV strings and DataFrames.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Tunables  -  nudge these if a particular lab's files aren't auto-detected
# --------------------------------------------------------------------------

SAMPLE_ID_PATTERNS = [
    r"^[A-Za-z]{1,6}[-_ ]?\d{2,}$",           # ABC1234, SMP-0001, DDH_120
    r"^\d{3,}$",                               # 100234
    r"^[A-Za-z0-9]{2,}[-_/][A-Za-z0-9-]+$",   # 21-DDH-045, BLK/STD
]

SAMPLE_HEADER_WORDS = {
    "sample", "sampleid", "sample_id", "sampleno", "sample no", "sample number",
    "sampid", "hole", "holeid", "hole_id", "dhid", "bhid", "id", "labid",
    "lab_id", "sample id",
}

HEADER_ROW_LABELS = ["element", "units", "method", "detection_limit"]

NON_NUMERIC_RESULT_TOKENS = {"", "-", "na", "n/a", "nd", "n.d.", "ins", "insuf"}


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class ParsedSif:
    delimiter: str
    analyte_headers: dict = field(default_factory=dict)   # label -> [per-analyte str]
    n_lead_cols: int = 1
    lead_col_names: list = field(default_factory=list)
    analytes: list = field(default_factory=list)
    data_rows: list = field(default_factory=list)         # aligned lead+analyte cells


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def sniff_delimiter(sample_text: str) -> str:
    """Pick the delimiter used by the data rows (comma / tab / semicolon / pipe)."""
    candidates = [",", "\t", ";", "|"]
    lines = [ln for ln in sample_text.splitlines() if ln.strip()]
    best, best_score = ",", -1.0
    for d in candidates:
        counts = [ln.count(d) for ln in lines]
        counts = [c for c in counts if c > 0]
        if not counts:
            continue
        mode = max(set(counts), key=counts.count)
        consistency = counts.count(mode) / len(counts)
        score = mode * consistency
        if score > best_score:
            best, best_score = d, score
    return best


def looks_like_sample_id(cell: str) -> bool:
    c = (cell or "").strip()
    if not c:
        return False
    return any(re.match(pat, c, re.IGNORECASE) for pat in SAMPLE_ID_PATTERNS)


def _is_number(cell: str) -> bool:
    cc = (cell or "").strip().lstrip("<>").replace(",", "")
    if cc == "":
        return False
    try:
        float(cc)
        return True
    except ValueError:
        return False


def numeric_fraction(cells: list) -> float:
    vals = [c for c in cells if (c or "").strip() != ""]
    if not vals:
        return 0.0
    return sum(1 for c in vals if _is_number(c)) / len(vals)


def find_first_data_row(rows: list) -> int:
    for i, row in enumerate(rows):
        if not row:
            continue
        first = row[0]
        rest = row[1:]
        if looks_like_sample_id(first) and numeric_fraction(rest) >= 0.5 and len(rest) >= 2:
            return i
        if len(rest) >= 3 and numeric_fraction(rest) >= 0.8 and (first or "").strip() != "":
            return i
    return -1


def detect_lead_columns(data_row: list) -> int:
    n = 0
    for cell in data_row:
        if _is_number(cell):
            break
        n += 1
        if n >= 4:
            break
    return max(1, n)


def _dedupe(names: list) -> list:
    out, seen = [], {}
    for k, raw in enumerate(names):
        name = (raw or "").strip() or f"analyte_{k+1}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        out.append(name)
    return out


def parse_text(text: str, forced_delim: str | None = None) -> ParsedSif:
    """Parse the full text of a SIF certificate into a ParsedSif."""
    delimiter = forced_delim or sniff_delimiter(text[:8192])
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [[(cell or "").strip() for cell in row] for row in reader]
    if not rows:
        raise ValueError("File is empty or unreadable.")

    data_start = find_first_data_row(rows)
    if data_start < 0:
        raise ValueError(
            "Could not locate a data row. Try forcing the delimiter, or the "
            "sample-id pattern may be unusual for this lab."
        )

    first_data = rows[data_start]
    n_lead = detect_lead_columns(first_data)
    n_analytes = len(first_data) - n_lead

    # Header block: non-blank rows immediately above the first data row.
    header_block = []
    i = data_start - 1
    while i >= 0 and rows[i] and any(c for c in rows[i]):
        if len(rows[i]) < max(2, n_lead + 1):
            break
        header_block.insert(0, rows[i])
        if len(header_block) >= len(HEADER_ROW_LABELS) + 1:
            break
        i -= 1

    def col(row, idx):
        return row[idx].strip() if idx < len(row) else ""

    # A trailing header row whose first cell is a sample-header word is the
    # column-label row; use it to name the lead columns.
    lead_names = ["sample_id"] + [f"lead_{k}" for k in range(1, n_lead)]
    analyte_label_row = None
    if header_block:
        bottom = header_block[-1]
        if bottom and bottom[0].strip().lower() in SAMPLE_HEADER_WORDS:
            analyte_label_row = header_block.pop()
            lead_names = [
                (c.strip() or f"lead_{k}")
                for k, c in enumerate(analyte_label_row[:n_lead])
            ]

    analyte_headers = {}
    for offset, hrow in enumerate(header_block):
        label = HEADER_ROW_LABELS[offset] if offset < len(HEADER_ROW_LABELS) else f"header_{offset}"
        analyte_headers[label] = [col(hrow, n_lead + j) for j in range(n_analytes)]

    if "element" in analyte_headers and any(analyte_headers["element"]):
        analytes = analyte_headers["element"]
    elif analyte_label_row is not None:
        analytes = [col(analyte_label_row, n_lead + j) for j in range(n_analytes)]
    else:
        analytes = [f"analyte_{j+1}" for j in range(n_analytes)]
    analytes = _dedupe(analytes)

    data_rows = []
    for row in rows[data_start:]:
        if not row or not any(c for c in row):
            continue
        if not (looks_like_sample_id(row[0]) or numeric_fraction(row[n_lead:]) >= 0.5):
            continue
        data_rows.append([col(row, k) for k in range(n_lead + n_analytes)])

    return ParsedSif(
        delimiter=delimiter,
        analyte_headers=analyte_headers,
        n_lead_cols=n_lead,
        lead_col_names=lead_names,
        analytes=analytes,
        data_rows=data_rows,
    )


# --------------------------------------------------------------------------
# Output helpers
# --------------------------------------------------------------------------

def result_flag(raw: str) -> str:
    low = (raw or "").strip().lower()
    if raw.startswith("<"):
        return "below_detection"
    if raw.startswith(">"):
        return "above_range"
    if low in NON_NUMERIC_RESULT_TOKENS:
        return "not_reported"
    return ""


def to_wide_csv(p: ParsedSif) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(list(p.lead_col_names) + list(p.analytes))
    for row in p.data_rows:
        w.writerow(row)
    return buf.getvalue()


def to_long_csv(p: ParsedSif) -> str:
    units = p.analyte_headers.get("units", [])
    methods = p.analyte_headers.get("method", [])
    dls = p.analyte_headers.get("detection_limit", [])

    def at(seq, j):
        return seq[j] if j < len(seq) else ""

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(list(p.lead_col_names)
               + ["analyte", "value", "units", "method", "detection_limit", "flag"])
    for row in p.data_rows:
        lead = row[: p.n_lead_cols]
        for j, analyte in enumerate(p.analytes):
            raw = row[p.n_lead_cols + j] if (p.n_lead_cols + j) < len(row) else ""
            w.writerow(lead + [analyte, raw, at(units, j), at(methods, j), at(dls, j), result_flag(raw)])
    return buf.getvalue()


def to_wide_df(p: ParsedSif):
    import pandas as pd
    cols = list(p.lead_col_names) + list(p.analytes)
    return pd.DataFrame(p.data_rows, columns=cols)


def analyte_table_df(p: ParsedSif):
    """Small table of analyte / units / method / detection limit for verification."""
    import pandas as pd
    data = {"element": list(p.analytes)}
    for label in ("units", "method", "detection_limit"):
        seq = p.analyte_headers.get(label, [])
        data[label] = [seq[j] if j < len(seq) else "" for j in range(len(p.analytes))]
    return pd.DataFrame(data)


def diagnostic(p: ParsedSif) -> dict:
    names = {",": "comma", "\t": "tab", ";": "semicolon", "|": "pipe"}
    return {
        "delimiter": names.get(p.delimiter, repr(p.delimiter)),
        "lead_columns": p.n_lead_cols,
        "lead_names": p.lead_col_names,
        "analyte_count": len(p.analytes),
        "sample_count": len(p.data_rows),
        "header_rows": list(p.analyte_headers.keys()),
    }
