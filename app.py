# -*- coding: utf-8 -*-
"""
Invoice Extraction Portal — Streamlit frontend.

Run with:  streamlit run app.py

Each uploaded PDF → one Excel file.
Multiple uploads → bundled zip download.
"""

import io
import os
import zipfile
from datetime import datetime

import pandas as pd
import streamlit as st

from excel_writer import generate_invoice_excel
from extractor import extract_from_pdf
from parser import extract_best_table, extract_invoice_meta

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Invoice Extraction Portal",
    page_icon="📄",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("📄 Invoice Extraction Portal")
st.markdown(
    "Upload digital PDF invoices — each invoice is extracted and saved as its own **Excel file**."
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    debug_mode = st.checkbox("🐛 Debug Mode (show raw extracted text)", value=False)
    st.markdown("---")
    st.markdown(
        "**How it works:**\n"
        "- Finds the main table in each PDF\n"
        "- Copies it into Excel exactly as-is\n"
        "- No fixed columns required\n"
        "- Works with any invoice format\n"
    )
    st.caption("Supports digital (text-based) PDFs only.")

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
st.subheader("📁 Upload Invoices")
uploaded_files = st.file_uploader(
    "Choose PDF files",
    type=["pdf"],
    accept_multiple_files=True,
    help="Upload one or more digital PDF invoice files",
)

if uploaded_files:
    st.info(f"**{len(uploaded_files)}** file(s) selected.")

    if st.button("🚀 Process Invoices", type="primary", use_container_width=True):

        results: list[dict] = []   # {filename, status, remarks, excel_path, table_data, meta}
        raw_texts: dict[str, str] = {}

        progress_bar       = st.progress(0)
        status_placeholder = st.empty()

        for idx, uploaded_file in enumerate(uploaded_files):
            fname = uploaded_file.name
            status_placeholder.text(
                f"Processing {idx + 1}/{len(uploaded_files)}: {fname}"
            )

            # Save PDF to disk
            save_path = os.path.join(UPLOAD_DIR, fname)
            with open(save_path, "wb") as fh:
                fh.write(uploaded_file.read())

            # Extract text + tables
            extraction = extract_from_pdf(save_path)

            if not extraction["success"]:
                results.append({
                    "filename":   fname,
                    "status":     "Failed",
                    "remarks":    extraction.get("error", "Extraction failed"),
                    "excel_path": None,
                    "table_data": None,
                    "meta":       {},
                })
                progress_bar.progress((idx + 1) / len(uploaded_files))
                continue

            raw_texts[fname] = extraction["text"]

            # Parse table (as-is) + invoice metadata
            table_data   = extract_best_table(extraction["tables"])
            invoice_meta = extract_invoice_meta(extraction["text"])

            if not table_data["found"]:
                results.append({
                    "filename":   fname,
                    "status":     "Partial",
                    "remarks":    "No table detected in PDF",
                    "excel_path": None,
                    "table_data": table_data,
                    "meta":       invoice_meta,
                })
                progress_bar.progress((idx + 1) / len(uploaded_files))
                continue

            # Generate Excel
            stem         = os.path.splitext(fname)[0]
            ts           = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_name   = f"{stem}_{ts}.xlsx"
            excel_path   = os.path.join(OUTPUT_DIR, excel_name)

            try:
                generate_invoice_excel(
                    table_data      = table_data,
                    invoice_meta    = invoice_meta,
                    output_path     = excel_path,
                    source_filename = fname,
                )
                results.append({
                    "filename":   fname,
                    "status":     "Success",
                    "remarks":    f"{len(table_data['rows'])} rows × {table_data['n_cols']} cols extracted",
                    "excel_path": excel_path,
                    "table_data": table_data,
                    "meta":       invoice_meta,
                })
            except Exception as e:
                results.append({
                    "filename":   fname,
                    "status":     "Failed",
                    "remarks":    f"Excel write error: {e}",
                    "excel_path": None,
                    "table_data": table_data,
                    "meta":       invoice_meta,
                })

            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_placeholder.text("✅ All files processed.")

        # ----------------------------------------------------------------
        # Summary metrics
        # ----------------------------------------------------------------
        st.markdown("---")
        st.subheader("📊 Processing Summary")

        total   = len(results)
        success = sum(1 for r in results if r["status"] == "Success")
        partial = sum(1 for r in results if r["status"] == "Partial")
        failed  = sum(1 for r in results if r["status"] == "Failed")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Files", total)
        c2.metric("✅ Success",  success)
        c3.metric("⚠️ Partial",  partial)
        c4.metric("❌ Failed",   failed)

        # ----------------------------------------------------------------
        # Per-invoice results
        # ----------------------------------------------------------------
        st.markdown("---")
        st.subheader("📋 Results per Invoice")

        for r in results:
            status_icon = {"Success": "✅", "Partial": "⚠️", "Failed": "❌"}.get(r["status"], "")
            with st.expander(f"{status_icon} {r['filename']}  —  {r['status']}"):

                # Invoice meta
                if r["meta"]:
                    meta_cols = st.columns(len(r["meta"]))
                    for col, (k, v) in zip(meta_cols, r["meta"].items()):
                        col.metric(k, v)

                # Table preview
                if r["table_data"] and r["table_data"]["found"]:
                    td = r["table_data"]
                    n  = len(td["headers"])
                    df = pd.DataFrame(
                        [(row + [""] * (n - len(row)))[:n] for row in td["rows"]],
                        columns=td["headers"],
                    )
                    st.dataframe(df, use_container_width=True, height=300)
                    st.caption(r["remarks"])
                else:
                    st.warning(r["remarks"])

                # Per-file download button
                if r["excel_path"] and os.path.exists(r["excel_path"]):
                    with open(r["excel_path"], "rb") as fh:
                        st.download_button(
                            label=f"⬇️ Download {os.path.basename(r['excel_path'])}",
                            data=fh.read(),
                            file_name=os.path.basename(r["excel_path"]),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{r['filename']}",
                        )

        # ----------------------------------------------------------------
        # Debug: raw text
        # ----------------------------------------------------------------
        if debug_mode and raw_texts:
            st.markdown("---")
            st.subheader("🐛 Raw Extracted Text")
            for fname, text in raw_texts.items():
                with st.expander(f"📄 {fname}"):
                    st.text_area("", text, height=280, key=f"raw_{fname}")

        # ----------------------------------------------------------------
        # Bulk download (zip) when multiple invoices
        # ----------------------------------------------------------------
        successful = [r for r in results if r["excel_path"] and os.path.exists(r["excel_path"])]
        if len(successful) > 1:
            st.markdown("---")
            st.subheader("📦 Download All as ZIP")
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for r in successful:
                    zf.write(r["excel_path"], arcname=os.path.basename(r["excel_path"]))
            zip_buffer.seek(0)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label=f"⬇️ Download All {len(successful)} Excel Files (.zip)",
                data=zip_buffer.read(),
                file_name=f"invoices_{ts}.zip",
                mime="application/zip",
                use_container_width=True,
                type="primary",
            )

else:
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 60px 20px;
            background: #f0f2f6;
            border-radius: 12px;
            margin-top: 24px;
        ">
            <h3 style="margin-bottom:8px">👆 Upload PDF invoices to get started</h3>
            <p style="color:#555">Each invoice gets its own Excel file — download individually or as a ZIP</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
