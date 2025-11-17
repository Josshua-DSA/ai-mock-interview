"""
Export / Serialization Utilities
"""
from typing import Dict, Optional
import json
import streamlit as st


def export_to_json(data: Dict, filename: str = "interview_result.json") -> Optional[str]:
    """Export data to JSON string (untuk di-download di Streamlit)"""
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        return json_str
    except Exception as e:
        st.error(f"Error saat export ke JSON: {str(e)}")
        return None
