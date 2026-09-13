"""SIF Certificate to CSV — drop an assay-lab SIF certificate in, get CSV out.

Wraps pyrpa.sif_convert. Runs fully in memory (no disk writes), so it works
on Streamlit Cloud. Widget keys are namespaced per uploaded file so multiple
certificates can be converted in one go without duplicate-key errors.
"""

import streamlit as st

from pyrpa import sif_convert

st.title("SIF Certificate → CSV")
st.markdown(
    "Convert assay-lab **SIF certificates** (the Standard Interchange Format "
    "files from ALS, SGS, Bureau Veritas, Intertek, etc.) into clean CSV. "
    "Drop one or more files below."
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


for idx, up in enumerate(uploaded):
    stem = up.name.rsplit(".", 1)[0]
    with st.expander(up.name, expanded=(len(uploaded) == 1)):
        try:
            text = _decode(up.getvalue())
            parsed = sif_convert.parse_text(text, forced_delim)
        except Exception as exc:  # noqa: BLE001 — show a clear message per file
            st.error(f"Could not parse **{up.name}**: {exc}")
            st.caption(
                "Tip: try forcing the delimiter in the sidebar. If it still "
                "fails, the header layout may be unusual — share a redacted "
                "sample (structure only, fake values) so the parser can be tuned."
            )
            continue

        diag = sif_convert.diagnostic(parsed)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Format", "fixed width" if diag["format"] == "fixed_width" else diag["delimiter"])
        c2.metric("Certificate", diag["certificate"] or "—")
        c3.metric("Analyte columns", diag["analyte_count"])
        c4.metric("Rows (incl. QC)", diag["sample_count"])

        if parsed.metadata:
            with st.popover("Certificate details"):
                st.dataframe(sif_convert.metadata_df(parsed), use_container_width=True, hide_index=True)

        st.markdown("**Detected columns** — check element / method / units line up before trusting the output:")
        st.dataframe(sif_convert.analyte_table_df(parsed), use_container_width=True, hide_index=True)

        st.markdown("**Data preview** (first 20 rows):")
        wide_df = sif_convert.to_wide_df(parsed)
        st.dataframe(wide_df.head(20), use_container_width=True, hide_index=True)

        wide_csv = sif_convert.to_wide_csv(parsed)
        long_csv = sif_convert.to_long_csv(parsed)
        d1, d2 = st.columns(2)
        d1.download_button(
            "⬇️ Download wide CSV",
            data=wide_csv,
            file_name=f"{stem}_wide.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"sif_wide_{idx}",
            help="One row per sample, one column per analyte.",
        )
        d2.download_button(
            "⬇️ Download long CSV",
            data=long_csv,
            file_name=f"{stem}_long.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"sif_long_{idx}",
            help="Tidy: one row per (sample, analyte) with units, method, detection limit, flag.",
        )
