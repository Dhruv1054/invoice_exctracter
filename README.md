# Invoice Extraction Portal

A simple, free, open-source MVP for extracting key fields from digital PDF invoices and exporting them to Excel.

---

## Features

- Upload one or multiple digital PDF invoices
- Extracts: Invoice Number, Date, Customer/Vendor Name, PO Number, Taxable/GST/Total amounts
- Exports to colour-coded `.xlsx` with a Summary sheet
- Detects duplicate invoice numbers
- Debug mode to inspect raw extracted text
- 100% free — no paid APIs

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

---

## Project Structure

```
invoice_extracter/
├── app.py            # Streamlit UI + main orchestration
├── extractor.py      # PDF text extraction (pdfplumber)
├── parser.py         # Regex-based field parsing
├── excel_writer.py   # Excel generation + formatting (openpyxl)
├── utils.py          # Date normalisation, number cleaning
├── uploads/          # Temp storage for uploaded PDFs
├── outputs/          # Generated Excel files
├── requirements.txt
└── README.md
```

---

## Extracted Fields

| Column | Description |
|---|---|
| File Name | Original PDF filename |
| Customer Name | Billed-to party |
| Vendor Name | Seller / issuer |
| Invoice Number | Invoice / bill number |
| Invoice Date | Normalised to DD/MM/YYYY |
| PO Number | Purchase order reference |
| Taxable Amount | Pre-tax subtotal |
| GST Amount | Tax amount |
| Total Amount | Grand total / amount due |
| Status | Success / Partial / Failed |
| Remarks | Missing fields or duplicate flags |

---

## Status Codes

| Status | Meaning |
|---|---|
| **Success** | All fields extracted |
| **Partial** | Non-critical fields missing |
| **Failed** | Critical fields (Invoice # or Total) missing, or text extraction failed |

---

## Extending the Parser

To add support for a new invoice format, open `parser.py` and add regex patterns to the relevant field list inside `PATTERNS`. Patterns are tried in order — add more specific patterns first.

---

## Future Roadmap

- [ ] OCR fallback for scanned PDFs (Tesseract)
- [ ] Customer-specific template matching
- [ ] Power BI / dashboard connector
- [ ] Internal deployment (Docker)
