"""
Main Application Entry Point
AI Interview Training System Pro
"""
import streamlit as st
from datetime import datetime
import time

# Import configurations
from config.settings import CONFIG

# Import services
from database.manager import DatabaseManager
from services.llm_service import LLMService
from services.visualizations_service import VisualizationService

# Import UI components
from ui.components import render_header, render_sidebar

# Import pages
from ui.pages.input_page import show_input_page
from ui.pages.interview_page import show_interview_page
from ui.pages.results_page import show_results_page
from ui.pages.history_page import show_history_page
from ui.pages.analytics_page import show_analytics_page


def init_session_state():
    """Initialize session state variables"""
    default_state = {
        'user_id': f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'stage': 'input',
        'questions': [],
        'answers': [],
        'answer_metadata': [],
        'current_question_idx': 0,
        'interview_start_time': None,
        'question_start_time': None,
        'model_choice': "gpt-4o",
        'difficulty': "Sedang",
        'enable_voice': False,
        'enable_camera': False,
        'enable_timer': True
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    """Main application function"""
    
    # Page configuration
    st.set_page_config(
        page_title="AI Interview Training Pro",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            font-weight: 600;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    init_session_state()
    
    # Initialize services
    db = DatabaseManager()
    llm = LLMService(model=st.session_state.model_choice)
    
    # Render header
    render_header()
    
    # Render sidebar and get settings
    model_choice, difficulty, enable_voice, enable_camera, enable_timer = render_sidebar(db)
    
    # Update session state with settings
    st.session_state.model_choice = model_choice
    st.session_state.difficulty = difficulty
    st.session_state.enable_voice = enable_voice
    st.session_state.enable_camera = enable_camera
    st.session_state.enable_timer = enable_timer
    
    # Route to appropriate page based on stage
    stage = st.session_state.get('stage', 'input')
    
    if stage == 'input':
        show_input_page(db, llm)
    elif stage == 'interview':
        show_interview_page(db, llm)
    elif stage == 'results':
        show_results_page(db, llm)
    elif stage == 'history':
        show_history_page(db)
    elif stage == 'analytics':
        show_analytics_page(db)
    else:
        st.error(f"Unknown stage: {stage}")
        st.session_state.stage = 'input'
        st.rerun()


if __name__ == "__main__":
    main()