"""
PDF Utilities
"""
from typing import Optional
import streamlit as st

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


def extract_text_from_pdf(pdf_file) -> Optional[str]:
    """Extract text from uploaded PDF file"""
    if PyPDF2 is None:
        st.error("❌ PyPDF2 belum terinstall. Jalankan: pip install PyPDF2")
        return None
    
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error membaca PDF: {str(e)}")
        return None
