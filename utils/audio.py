"""
Audio & Text-to-Speech Utilities
"""
from typing import Optional
from io import BytesIO
import base64
import streamlit as st

try:
    from gtts import gTTS
except ImportError:
    gTTS = None


def text_to_speech(text: str, lang: str = 'id') -> Optional[bytes]:
    """Convert text to speech, return bytes mp3"""
    if gTTS is None:
        st.warning("⚠️ gTTS belum terinstall. Jalankan: pip install gTTS")
        return None
    
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        st.error(f"Error generate audio: {str(e)}")
        return None


def autoplay_audio(audio_bytes: bytes):
    """Autoplay audio di browser dengan HTML sederhana"""
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
