# ============================================
# ui/pages/__init__.py
# ============================================
"""
UI Pages Module
"""
from .input_page import show_input_page
from .interview_page import show_interview_page
from .results_page import show_results_page
from .history_page import show_history_page
from .analytics_page import show_analytics_page

__all__ = [
    'show_input_page',
    'show_interview_page',
    'show_results_page',
    'show_history_page',
    'show_analytics_page'
]