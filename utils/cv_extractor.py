"""
CV Utilities (validasi & nanti bisa ditambah text mining)
"""
from typing import Tuple


def validate_cv(cv_text: str) -> Tuple[bool, str]:
    """Validate CV text"""
    if not cv_text or len(cv_text.strip()) < 100:
        return False, "CV terlalu singkat. Minimal 100 karakter."
    
    if len(cv_text) > 10000:
        return False, "CV terlalu panjang. Maksimal 10.000 karakter."
    
    cv_lower = cv_text.lower()
    has_experience = any(word in cv_lower for word in ['pengalaman', 'experience', 'kerja', 'work'])
    has_skills = any(word in cv_lower for word in ['skill', 'kemampuan', 'keahlian', 'kompeten'])
    
    if not (has_experience or has_skills):
        return False, "CV harus mencantumkan pengalaman atau keahlian."
    
    return True, "CV valid"
