import pdfplumber
import logging

logger = logging.getLogger(__name__)


def extract_from_pdf(file_path: str) -> dict:
    """
    Extract both text and tables from a PDF file using pdfplumber.

    Returns:
        success  (bool)
        text     (str)           — full concatenated page text
        pages    (list[dict])    — per-page text
        tables   (list[dict])    — {page_num, data: list[list[str|None]]}
        error    (str | None)
    """
    result = {
        "success": False,
        "text": "",
        "pages": [],
        "tables": [],
        "error": None,
    }
    try:
        with pdfplumber.open(file_path) as pdf:
            all_text = []
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                result["pages"].append({"page_num": i + 1, "text": page_text})
                all_text.append(page_text)

                # Extract tables on this page
                for table in (page.extract_tables() or []):
                    if table:
                        result["tables"].append({"page_num": i + 1, "data": table})

            result["text"] = "\n".join(all_text)
            result["success"] = bool(result["text"].strip())
            if not result["success"]:
                result["error"] = "No text found — PDF may be image-based (scanned)"

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Extraction failed for {file_path}: {e}")
    return result


# Keep old name as alias so nothing else breaks
def extract_text_from_pdf(file_path: str) -> dict:
    return extract_from_pdf(file_path)
