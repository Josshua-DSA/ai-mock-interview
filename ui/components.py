"""
Reusable UI Components
"""
import streamlit as st
from typing import List
from database.manager import DatabaseManager
from config.settings import JobCategory


def render_header():
    """Render application header"""
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .main-header h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
        }
        .main-header p {
            color: rgba(255, 255, 255, 0.9);
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            font-weight: 600;
        }
        </style>
        <div class="main-header">
            <h1>🎯 AI Interview Training System Pro</h1>
            <p>Latihan interview AI-powered dengan feedback real-time</p>
        </div>
    """, unsafe_allow_html=True)


def render_sidebar(db: DatabaseManager):
    """Render enhanced sidebar"""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/667eea/ffffff?text=InterviewAI", 
                 use_container_width=True)
        
        st.markdown("---")
        
        # Settings
        st.subheader("⚙️ Pengaturan")
        model_choice = st.selectbox(
            "Model AI",
            ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            help="Pilih model AI untuk interview"
        )
        
        difficulty = st.select_slider(
            "Tingkat Kesulitan",
            options=["Mudah", "Sedang", "Sulit", "Ahli"],
            value="Sedang"
        )
        
        enable_voice = st.checkbox("🎤 Text-to-Speech", value=False)
        enable_camera = st.checkbox("📹 Video Mode", value=False)
        enable_timer = st.checkbox("⏱️ Timer", value=True)
        
        st.markdown("---")
        
        # Quick stats
        if 'user_id' in st.session_state:
            st.subheader("📊 Quick Stats")
            analytics = db.get_analytics_data(st.session_state.user_id)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Interviews", analytics['total_interviews'])
            with col2:
                st.metric("Avg Score", f"{analytics['avg_score']:.1f}")
        
        st.markdown("---")
        
        # Navigation
        st.subheader("🧭 Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.stage = 'input'
            st.rerun()
        
        if st.button("📚 History", use_container_width=True):
            st.session_state.stage = 'history'
            st.rerun()
        
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state.stage = 'analytics'
            st.rerun()
        
        st.markdown("---")
        
        # Info
        st.info("""
        **Version:** 2.1 Pro
        
        **Tech Stack:**
        - 🤖 OpenAI GPT-4
        - 📊 Plotly Charts
        - 💾 SQLite
        - 🚀 Streamlit
        """)
        
        return model_choice, difficulty, enable_voice, enable_camera, enable_timer


def render_question_card(question: dict, question_num: int, total_questions: int):
    """Render interview question card"""
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 10px; margin: 1rem 0;'>
            <p style='color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;'>
                📌 {question['category'].upper()} • Question {question_num}/{total_questions}
            </p>
            <h2 style='color: white; margin: 0.5rem 0;'>{question['question']}</h2>
            <p style='color: rgba(255,255,255,0.7); margin: 0.5rem 0 0 0;'>
                💡 {question.get('context', '')}
            </p>
        </div>
    """, unsafe_allow_html=True)


def render_score_metrics(scores: dict, avg_score: float, passed: bool):
    """Render score metrics"""
    if passed:
        st.success(f"🎉 Passed! Score: {avg_score:.1f}/100")
    else:
        st.warning(f"💪 Keep Improving! Score: {avg_score:.1f}/100")
    
    col1, col2, col3, col4 = st.columns(4)
    score_items = list(scores.items())
    
    for i, (category, score) in enumerate(score_items[:4]):
        with [col1, col2, col3, col4][i]:
            st.metric(category.replace('_', ' ').title(), f"{score:.0f}")


def render_feedback_section(feedback: dict):
    """Render feedback section"""
    st.subheader("💬 Feedback")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("**✅ Strengths**")
        for strength in feedback.get('strengths', []):
            st.write(f"• {strength}")
    
    with col2:
        st.warning("**⚠️ Improvements**")
        for weakness in feedback.get('weaknesses', []):
            st.write(f"• {weakness}")