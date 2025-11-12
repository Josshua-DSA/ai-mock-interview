"""
Utility Helper Functions
"""
import hashlib
import time
import json
import base64
from datetime import datetime
from typing import Optional, Tuple, Dict
from io import BytesIO
import streamlit as st

# Optional imports
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None


class Utils:
    """Utility functions for the application"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"session_{timestamp}_{random_hash}"
    
    @staticmethod
    def extract_text_from_pdf(pdf_file) -> Optional[str]:
        """Extract text from uploaded PDF file"""
        if PyPDF2 is None:
            st.error("❌ PyPDF2 not installed. pip install PyPDF2")
            return None
        
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return None
    
    @staticmethod
    def validate_cv(cv_text: str) -> Tuple[bool, str]:
        """Validate CV text"""
        if not cv_text or len(cv_text.strip()) < 100:
            return False, "CV terlalu singkat. Minimal 100 karakter."
        
        if len(cv_text) > 10000:
            return False, "CV terlalu panjang. Maksimal 10.000 karakter."
        
        # Check for basic CV elements
        cv_lower = cv_text.lower()
        has_experience = any(word in cv_lower for word in ['pengalaman', 'experience', 'kerja', 'work'])
        has_skills = any(word in cv_lower for word in ['skill', 'kemampuan', 'keahlian', 'kompeten'])
        
        if not (has_experience or has_skills):
            return False, "CV harus mencantumkan pengalaman atau keahlian."
        
        return True, "CV valid"
    
    @staticmethod
    def text_to_speech(text: str, lang: str = 'id') -> Optional[bytes]:
        """Convert text to speech"""
        if gTTS is None:
            return None
        
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            st.error(f"Error generating speech: {str(e)}")
            return None
    
    @staticmethod
    def autoplay_audio(audio_bytes: bytes):
        """Autoplay audio in browser"""
        b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in readable format"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    
    @staticmethod
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
    
    @staticmethod
    def export_to_json(data: Dict, filename: str = "interview_result.json") -> Optional[str]:
        """Export data to JSON file"""
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            return json_str
        except Exception as e:
            st.error(f"Error exporting data: {str(e)}")
            return None