"""
Time & Session Utilities
"""
import hashlib
import time
from datetime import datetime


def generate_session_id() -> str:
    """Generate unique session ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    return f"session_{timestamp}_{random_hash}"


def format_duration(seconds: int) -> str:
    """Format duration in readable format"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}m {secs}s"


def calculate_grade(score: float) -> str:
    """Calculate letter grade from score"""
    if score >= 90:
        return "A (Excellent)"
    elif score >= 80:
        return "B (Very Good)"
    elif score >= 70:
        return "C (Good)"
    elif score >= 60:
        return "D (Fair)"
    else:
        return "E (Needs Improvement)"
