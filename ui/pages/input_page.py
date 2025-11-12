"""
Input Page - CV and Profile Input
"""
import streamlit as st
import time
from utils.helpers import Utils
from config.settings import JobCategory


def show_input_page(db, llm):
    """CV and profile input stage"""
    st.header("📝 Profile & Job Target")
    
    # CV Input Method Selection
    st.subheader("📄 CV Input Method")
    cv_input_method = st.radio(
        "Choose input method:",
        ["Type CV Text", "Upload PDF"],
        horizontal=True,
        key="cv_input_method"
    )
    
    # PDF Upload
    cv_text_from_pdf = ""
    if cv_input_method == "Upload PDF":
        uploaded_file = st.file_uploader(
            "📎 Upload CV (PDF)",
            type=['pdf'],
            help="Upload CV dalam format PDF"
        )
        
        if uploaded_file:
            with st.spinner("📖 Reading PDF..."):
                extracted_text = Utils.extract_text_from_pdf(uploaded_file)
                if extracted_text:
                    cv_text_from_pdf = extracted_text
                    st.success(f"✅ PDF loaded! ({len(cv_text_from_pdf)} chars)")
                    with st.expander("📄 Preview"):
                        st.text_area("Content", cv_text_from_pdf, height=200, disabled=True)
        else:
            st.info("👆 Upload your CV in PDF format")
    
    st.markdown("---")
    
    # Main Form
    with st.form("cv_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Your Profile")
            
            full_name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="john@example.com")
            
            col_exp, col_edu = st.columns(2)
            with col_exp:
                experience_years = st.number_input("Years Experience", 0, 50, 0)
            with col_edu:
                education = st.selectbox(
                    "Education",
                    ["SMA/SMK", "D3", "S1", "S2", "S3"]
                )
            
            st.markdown("---")
            
            # CV text input
            if cv_input_method == "Type CV Text":
                cv_text_manual = st.text_area(
                    "CV Content",
                    height=300,
                    placeholder="Enter your CV here...\n\n- Work experience\n- Education\n- Skills\n- Projects"
                )
            else:
                cv_text_manual = ""
                if cv_text_from_pdf:
                    st.success(f"✅ Using CV from PDF ({len(cv_text_from_pdf)} chars)")
        
        with col2:
            st.subheader("Job Target")
            
            target_job = st.text_input(
                "Position",
                placeholder="e.g., Software Engineer"
            )
            
            job_category = st.selectbox(
                "Category",
                [cat.value for cat in JobCategory]
            )
            
            skills = st.text_area(
                "Key Skills",
                height=100,
                placeholder="Python, JavaScript..."
            )
            
            st.info("💡 **Tips:**\n- Min 200 words\n- Include experience\n- List technologies")
        
        submitted = st.form_submit_button("🚀 Start Interview", type="primary")
    
    if submitted:
        # Determine CV source
        cv_text = cv_text_from_pdf if cv_input_method == "Upload PDF" else cv_text_manual
        
        # Validate
        if not cv_text:
            st.error("❌ CV cannot be empty!")
            return
        
        is_valid, message = Utils.validate_cv(cv_text)
        if not is_valid:
            st.error(f"❌ {message}")
            return
        
        if not target_job:
            st.error("❌ Please enter target position!")
            return
        
        with st.spinner("🔄 Analyzing CV and generating questions..."):
            # Save profile
            profile_data = {
                'full_name': full_name,
                'email': email,
                'cv_text': cv_text,
                'target_job': target_job,
                'job_category': job_category,
                'experience_years': experience_years,
                'education_level': education,
                'skills': skills.split(',') if skills else []
            }
            
            db.save_user_profile(st.session_state.user_id, profile_data)
            
            # Generate questions
            analysis_result = llm.analyze_cv_and_generate_questions(
                cv_text,
                target_job,
                st.session_state.difficulty
            )
            
            # Initialize session state
            st.session_state.cv_text = cv_text
            st.session_state.target_job = target_job
            st.session_state.profile_data = profile_data
            st.session_state.analysis = analysis_result.get('analysis', {})
            st.session_state.questions = analysis_result.get('questions', [])
            st.session_state.answers = []
            st.session_state.answer_metadata = []
            st.session_state.current_question_idx = 0
            st.session_state.session_id = Utils.generate_session_id()
            st.session_state.interview_start_time = time.time()
            st.session_state.question_start_time = time.time()
            st.session_state.stage = 'interview'
            
            st.success("✅ Analysis complete! Starting interview...")
            time.sleep(1)
            st.rerun()