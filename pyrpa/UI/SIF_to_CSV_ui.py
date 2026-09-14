"""SIF Certificate to CSV — drop assay-lab SIF certificates in, get CSV out.

Wraps pyrpa.sif_convert. Runs fully in memory (no disk writes), so it works
on Streamlit Cloud. Supports batch upload: multiple certificates are merged
into one combined wide CSV and one combined long CSV (row-stacked when the
columns match, union with a warning when they differ), with an optional
per-file .zip. Widget keys are namespaced so nothing collides.
"""

import importlib
import io
import os
import zipfile

import pandas as pd
import streamlit as st

from pyrpa import sif_convert

# Streamlit Cloud keeps the Python process alive across redeploys and only
# re-runs the entry script, so an imported module can stay pinned to an older
# cached copy even after a git deploy. This UI file is re-executed from disk on
# every run (via runpy), so reloading here guarantees the latest parser.
sif_convert = importlib.reload(sif_convert)


# ── Offline "Run locally" bundle ─────────────────────────────────────────────
# A hosted web page cannot open a terminal on the viewer's machine (browser
# sandbox). The next best thing: hand them a small, dependency-free bundle they
# can double-click. It reuses the SAME parser that runs here (read from disk at
# request time) so the offline result always matches the online one.

_CLI_WRAPPER = r'''#!/usr/bin/env python3
# Local CLI for the SLR Tools "SIF Certificate to CSV" converter.
# Bundled by the app's "Run locally" button. Standard library only.
# Usage:
#   python sif_to_csv.py FILE.sif [more.sif ...] [--outdir csv_out] [--merge]
# Or drag .sif files onto "Run SIF to CSV.bat".
import argparse, glob, os
import sif_convert


def read_text(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


def _stack(csvs):
    out, header = [], None
    for s in csvs:
        lines = s.splitlines()
        if not lines:
            continue
        if header is None:
            header = lines[0]
            out.append(header)
        out.extend(lines[1:])
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Convert assay-lab SIF certificates to CSV.")
    ap.add_argument("files", nargs="+", help="One or more .sif files (wildcards ok).")
    ap.add_argument("--outdir", default="csv_out")
    ap.add_argument("--merge", action="store_true", help="Also write combined_wide/long.csv.")
    ap.add_argument("--delimiter", default=None, help="Force a delimiter ('tab' for tab).")
    args = ap.parse_args()
    forced = "\t" if args.delimiter == "tab" else args.delimiter

    paths = []
    for pattern in args.files:
        hits = glob.glob(pattern)
        paths.extend(hits if hits else [pattern])

    os.makedirs(args.outdir, exist_ok=True)
    parsed = []
    for p in paths:
        if not os.path.isfile(p):
            print("[skip] not a file:", p)
            continue
        try:
            result = sif_convert.parse_text(read_text(p), forced)
        except Exception as exc:
            print("[FAIL]", p, "->", exc)
            continue
        parsed.append(result)
        base = os.path.splitext(os.path.basename(p))[0]
        with open(os.path.join(args.outdir, base + "_wide.csv"), "w", encoding="utf-8", newline="") as fh:
            fh.write(sif_convert.to_wide_csv(result))
        with open(os.path.join(args.outdir, base + "_long.csv"), "w", encoding="utf-8", newline="") as fh:
            fh.write(sif_convert.to_long_csv(result))
        print("[ok]", p, "->", base + "_wide.csv /", base + "_long.csv")

    if args.merge and parsed:
        with open(os.path.join(args.outdir, "combined_long.csv"), "w", encoding="utf-8", newline="") as fh:
            fh.write(_stack([sif_convert.to_long_csv(r) for r in parsed]))
        heads = {tuple(r.lead_col_names + r.analytes) for r in parsed}
        if len(heads) == 1:
            with open(os.path.join(args.outdir, "combined_wide.csv"), "w", encoding="utf-8", newline="") as fh:
                fh.write(_stack([sif_convert.to_wide_csv(r) for r in parsed]))
            print("[ok] merged", len(parsed), "files -> combined_wide.csv / combined_long.csv")
        else:
            print("[warn] files have different columns; wrote combined_long.csv only.")

    print("Done. Output in", os.path.abspath(args.outdir))


if __name__ == "__main__":
    main()
'''

_BAT_LAUNCHER = r'''@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title SIF Certificate to CSV
echo(
echo    SIF Certificate to CSV  (local runner)
echo(
where python >nul 2>nul || (
  echo    Python 3.9+ was not found on PATH.
  echo    Install it from https://www.python.org/downloads/ and tick
  echo    "Add python.exe to PATH", then run this again.
  echo(
  pause
  exit /b 1
)
if "%~1"=="" (
  echo    Tip: you can also drag your .sif files straight onto this .bat icon.
  echo(
  set /p "SRC=   Paste a .sif file or a folder path (blank to cancel): "
  if "!SRC!"=="" exit /b 0
  if exist "!SRC!\" (
    python sif_to_csv.py "!SRC!\*.sif" --outdir "!SRC!\csv_out" --merge
  ) else (
    python sif_to_csv.py "!SRC!" --outdir "%~dp0csv_out"
  )
) else (
  python sif_to_csv.py %* --outdir "%~dp0csv_out" --merge
)
echo(
echo    Done. Look in the csv_out folder.
pause
'''

_LOCAL_README = r'''SIF Certificate to CSV - local runner
=====================================

Offline copy of the SLR Tools "SIF Certificate to CSV" converter. It runs
entirely on your machine; nothing is uploaded anywhere.

Requirements: Python 3.9+ (https://www.python.org/downloads/).
No other install needed (standard library only).

Windows (easiest):
  1. Unzip this folder somewhere.
  2. Double-click "Run SIF to CSV.bat", or drag your .sif files onto it.
  3. CSVs appear in a "csv_out" folder.
  (If SmartScreen warns about the .bat, choose "More info" then "Run anyway".)

Command line (any OS):
  python sif_to_csv.py FILE.sif [more.sif ...] --outdir csv_out
  python sif_to_csv.py *.sif --outdir csv_out --merge

Per file: <name>_wide.csv and <name>_long.csv
With --merge: combined_wide.csv and combined_long.csv
'''


def _local_bundle_bytes() -> bytes:
    """Zip the current parser + a tiny CLI + a Windows launcher for offline use."""
    with open(sif_convert.__file__, "r", encoding="utf-8") as fh:
        core_src = fh.read()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("sif_convert.py", core_src)
        zf.writestr("sif_to_csv.py", _CLI_WRAPPER)
        zf.writestr("Run SIF to CSV.bat", _BAT_LAUNCHER)
        zf.writestr("README.txt", _LOCAL_README)
    return buf.getvalue()


st.title("SIF Certificate → CSV")
st.markdown(
    "Convert assay-lab **SIF certificates** (the Standard Interchange Format "
    "files from ALS, SGS, Bureau Veritas, Intertek, etc.) into clean CSV. "
    "Drop one or more files below — multiple files are merged into one combined CSV."
)

DELIM_CHOICES = {
    "Auto-detect": None,
    "Comma ( , )": ",",
    "Tab": "\t",
    "Semicolon ( ; )": ";",
    "Pipe ( | )": "|",
}

with st.sidebar:
    st.markdown("## Options")
    delim_label = st.selectbox(
        "Delimiter",
        list(DELIM_CHOICES.keys()),
        index=0,
        help="Leave on Auto-detect unless the columns come out wrong.",
        key="sif_delim",
    )
    forced_delim = DELIM_CHOICES[delim_label]
    make_zip = st.checkbox(
        "Also offer per-file .zip",
        value=False,
        help="Build a zip of each file's own wide + long CSVs, in addition to the merged output.",
        key="sif_zip",
    )

    with st.expander("🖥️ Run locally (offline)"):
        st.caption(
            "A web page can't open a terminal on your PC, so this gives you a small "
            "offline bundle instead. It runs on your machine and nothing is uploaded. "
            "Good for big batches or confidential data. Needs Python 3.9+ (no internet "
            "or install)."
        )
        st.download_button(
            "⬇️ Download local runner (.zip)",
            data=_local_bundle_bytes(),
            file_name="SIF-to-CSV-local.zip",
            mime="application/zip",
            use_container_width=True,
            key="run_local_zip",
        )
        st.markdown(
            "**How to use**\n"
            "1. Unzip the downloaded file into a folder.\n"
            "2. Double-click **Run SIF to CSV.bat**, or drag your `.sif` files onto it.\n"
            "3. If it asks, drag the files in or paste a folder path, then press Enter.\n"
            "4. Your CSVs land in a new **csv_out** folder (plus a combined file when "
            "you convert several)."
        )
        st.markdown(
            "**Prefer typing?** Put your `.sif` files in that folder, open it, click the "
            "address bar, type `cmd`, press Enter, then run:"
        )
        st.code("python sif_to_csv.py *.sif --outdir csv_out --merge", language="bash")
        st.caption(
            "First run only: if Windows SmartScreen warns, choose *More info* then "
            "*Run anyway*. If Python isn't found, install it from python.org and tick "
            '"Add python.exe to PATH".'
        )

uploaded = st.file_uploader(
    "SIF certificate file(s)",
    type=["sif", "csv", "txt"],
    accept_multiple_files=True,
    key="sif_upload",
    help="These stay on the server only for this session and are never stored.",
)

if not uploaded:
    st.info("Upload one or more .sif certificate files to begin.")
    st.stop()


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _stack_csv(csv_strings: list) -> str:
    """Concatenate CSV strings that share an identical header: keep the first
    header, drop the rest, append all data rows."""
    out, header = [], None
    for s in csv_strings:
        lines = s.splitlines()
        if not lines:
            continue
        if header is None:
            header = lines[0]
            out.append(header)
        out.extend(lines[1:])
    return "\n".join(out) + "\n"


# ── Parse every uploaded file ────────────────────────────────────────────────
results, errors = [], []
for up in uploaded:
    try:
        results.append((up.name, sif_convert.parse_text(_decode(up.getvalue()), forced_delim)))
    except Exception as exc:  # noqa: BLE001 — report per file, keep going
        errors.append((up.name, str(exc)))

if errors:
    st.warning(f"Could not parse {len(errors)} file(s) — they are excluded from the merge:")
    for name, msg in errors:
        st.write(f"- **{name}**: {msg}")
    st.caption(
        "Tip: try forcing the delimiter in the sidebar. If it still fails, the header "
        "layout may be unusual — share a redacted sample (structure only, fake values). "
        "You can also use **Run locally (offline)** in the sidebar to convert on your own machine."
    )

if not results:
    st.stop()

multi = len(results) > 1

# ── Combined output (batch) ──────────────────────────────────────────────────
if multi:
    st.subheader("Combined output")

    schemas = {tuple(p.lead_col_names + p.analytes) for _, p in results}
    same_cols = len(schemas) == 1

    long_combined = _stack_csv([sif_convert.to_long_csv(p) for _, p in results])
    if same_cols:
        wide_combined = _stack_csv([sif_convert.to_wide_csv(p) for _, p in results])
    else:
        frames = [sif_convert.to_wide_df(p) for _, p in results]
        wide_combined = pd.concat(frames, ignore_index=True).fillna("").to_csv(index=False)

    total_rows = sum(len(p.data_rows) for _, p in results)
    c1, c2, c3 = st.columns(3)
    c1.metric("Files merged", len(results))
    c2.metric("Total rows", total_rows)
    c3.metric("Columns", "consistent" if same_cols else "union (differ)")

    if same_cols:
        st.caption("All files share the same columns — merged by stacking rows.")
    else:
        st.warning(
            "Files have different column sets. The combined **wide** CSV uses the union of "
            "columns (blank where a file lacks one); the combined **long** CSV is unaffected. "
            "Each row carries its `certificate`, so you can always tell files apart."
        )

    st.markdown("**Combined preview** (first 20 rows of the wide table):")
    preview = pd.read_csv(io.StringIO(wide_combined), nrows=20, dtype=str, keep_default_na=False)
    st.dataframe(preview, use_container_width=True, hide_index=True)

    d1, d2 = st.columns(2)
    d1.download_button(
        "⬇️ Combined wide CSV",
        data=wide_combined,
        file_name="combined_wide.csv",
        mime="text/csv",
        use_container_width=True,
        key="cmb_wide",
        help="All samples from all files, one row per sample, one column per analyte.",
    )
    d2.download_button(
        "⬇️ Combined long CSV",
        data=long_combined,
        file_name="combined_long.csv",
        mime="text/csv",
        use_container_width=True,
        key="cmb_long",
        help="All measurements from all files, one row per (sample, analyte).",
    )

    if make_zip:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, p in results:
                stem = name.rsplit(".", 1)[0]
                zf.writestr(f"{stem}_wide.csv", sif_convert.to_wide_csv(p))
                zf.writestr(f"{stem}_long.csv", sif_convert.to_long_csv(p))
        st.download_button(
            "⬇️ Each file separately (.zip)",
            data=buf.getvalue(),
            file_name="sif_csv_export.zip",
            mime="application/zip",
            use_container_width=True,
            key="cmb_zip",
        )

    st.divider()
    st.caption("Per-file details below (for spot-checking each certificate).")

# ── Per-file detail ──────────────────────────────────────────────────────────
for idx, (name, parsed) in enumerate(results):
    with st.expander(name, expanded=(not multi)):
        diag = sif_convert.diagnostic(parsed)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Format", "fixed width" if diag["format"] == "fixed_width" else diag["delimiter"])
        c2.metric("Certificate", diag["certificate"] or "—")
        c3.metric("Analyte columns", diag["analyte_count"])
        c4.metric("Rows (incl. QC)", diag["sample_count"])

        if not multi:
            # Full detail for a single upload; kept light in batch mode.
            if parsed.metadata:
                with st.popover("Certificate details"):
                    st.dataframe(sif_convert.metadata_df(parsed), use_container_width=True, hide_index=True)

            st.markdown("**Detected columns** — check element / method / units line up before trusting the output:")
            st.dataframe(sif_convert.analyte_table_df(parsed), use_container_width=True, hide_index=True)

            st.markdown("**Data preview** (first 20 rows):")
            st.dataframe(sif_convert.to_wide_df(parsed).head(20), use_container_width=True, hide_index=True)

            stem = name.rsplit(".", 1)[0]
            d1, d2 = st.columns(2)
            d1.download_button(
                "⬇️ Download wide CSV",
                data=sif_convert.to_wide_csv(parsed),
                file_name=f"{stem}_wide.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"sif_wide_{idx}",
                help="One row per sample, one column per analyte.",
            )
            d2.download_button(
                "⬇️ Download long CSV",
                data=sif_convert.to_long_csv(parsed),
                file_name=f"{stem}_long.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"sif_long_{idx}",
                help="Tidy: one row per (sample, analyte) with units, method, detection limit, flag.",
            )
        else:
            meta = parsed.metadata or {}
            bits = [f"**{k}:** {meta[k]}" for k in ("CLIENT", "PROJECT", "DATE COMPLETED") if k in meta]
            if bits:
                st.caption(" · ".join(bits))
