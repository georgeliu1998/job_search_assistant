"""
PDF processing utilities for extracting text from uploaded files.
"""

import logging
from typing import Optional

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from src.utils.logging import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from uploaded PDF file.

    Args:
        pdf_file: Streamlit uploaded file object or file-like object

    Returns:
        Extracted text as string

    Raises:
        ImportError: If PyPDF2 is not installed
        Exception: If PDF processing fails
    """
    if PyPDF2 is None:
        raise ImportError(
            "PyPDF2 is required for PDF processing. "
            "Please install it with: pip install PyPDF2"
        )

    if pdf_file is None:
        return ""

    try:
        # Reset file pointer to beginning
        pdf_file.seek(0)

        # Create PDF reader
        reader = PyPDF2.PdfReader(pdf_file)

        # Extract text from all pages
        text_parts = []
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    text_parts.append(page_text)
                    logger.debug(
                        f"Extracted {len(page_text)} characters from page {page_num + 1}"
                    )
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")

        full_text = "\n\n".join(text_parts)

        logger.info(
            f"Successfully extracted {len(full_text)} characters from {len(text_parts)} pages"
        )
        return full_text.strip()

    except Exception as e:
        logger.error(f"Failed to process PDF: {e}")
        raise Exception(f"PDF processing failed: {str(e)}")


def validate_pdf_file(pdf_file) -> bool:
    """
    Validate that the uploaded file is a readable PDF.

    Args:
        pdf_file: Streamlit uploaded file object

    Returns:
        True if valid PDF, False otherwise
    """
    if pdf_file is None:
        return False

    if PyPDF2 is None:
        logger.warning("PyPDF2 not available for PDF validation")
        return False

    try:
        pdf_file.seek(0)
        reader = PyPDF2.PdfReader(pdf_file)

        # Try to access first page to validate
        if len(reader.pages) > 0:
            _ = reader.pages[0]
            return True
        else:
            logger.warning("PDF file contains no pages")
            return False

    except Exception as e:
        logger.warning(f"PDF validation failed: {e}")
        return False


def get_pdf_info(pdf_file) -> Optional[dict]:
    """
    Get basic information about the PDF file.

    Args:
        pdf_file: Streamlit uploaded file object

    Returns:
        Dictionary with PDF info or None if processing fails
    """
    if not validate_pdf_file(pdf_file):
        return None

    try:
        pdf_file.seek(0)
        reader = PyPDF2.PdfReader(pdf_file)

        info = {
            "num_pages": len(reader.pages),
            "title": (
                getattr(reader.metadata, "title", None) if reader.metadata else None
            ),
            "author": (
                getattr(reader.metadata, "author", None) if reader.metadata else None
            ),
            "subject": (
                getattr(reader.metadata, "subject", None) if reader.metadata else None
            ),
        }

        # Estimate text length
        total_chars = 0
        for page in reader.pages[:3]:  # Sample first 3 pages
            try:
                total_chars += len(page.extract_text())
            except:
                continue

        info["estimated_total_chars"] = (
            total_chars * len(reader.pages) // min(3, len(reader.pages))
        )

        return info

    except Exception as e:
        logger.error(f"Failed to get PDF info: {e}")
        return None
