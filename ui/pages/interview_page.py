"""
Interview Page - Interactive Interview Session
"""
import streamlit as st
import time
from config.settings import CONFIG
from utils.helpers import Utils
from ui.components import render_question_card


def show_interview_page(db, llm):
    """Enhanced interview stage with camera and voice"""
    st.header("🎤 Interview in Progress")
    
    # Get settings
    use_camera = st.session_state.get('enable_camera', False)
    use_voice = st.session_state.get('enable_voice', False)
    use_timer = st.session_state.get('enable_timer', True)
    
    # Progress tracking
    total_questions = len(st.session_state.questions)
    current_idx = st.session_state.current_question_idx
    progress = (current_idx) / total_questions if total_questions > 0 else 0
    
    # Progress bar and metrics
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.progress(progress)
    with col2:
        st.metric("Question", f"{current_idx + 1}/{total_questions}")
    with col3:
        if use_timer and st.session_state.interview_start_time:
            elapsed = int(time.time() - st.session_state.interview_start_time)
            st.metric("Time", Utils.format_duration(elapsed))
        else:
            st.metric("Time", "N/A")
    
    # Check if interview is complete
    if current_idx >= total_questions:
        st.success("✅ Interview completed! Moving to results...")
        time.sleep(1)
        st.session_state.stage = 'results'
        st.rerun()
        return
    
    current_q = st.session_state.questions[current_idx]
    
    # Camera section
    if use_camera:
        st.markdown("---")
        col_cam1, col_cam2 = st.columns([2, 1])
        with col_cam1:
            camera_image = st.camera_input(
                "📹 Video Interview Mode", 
                key=f"camera_{current_idx}"
            )
            if camera_image:
                st.caption("✅ Camera active - Interview is being recorded")
        with col_cam2:
            st.info("""
            **📹 Camera Tips:**
            - Look at camera
            - Good lighting
            - Professional background
            - Smile & be confident!
            """)
        st.markdown("---")
    
    # Question card
    render_question_card(current_q, current_idx + 1, total_questions)
    
    # Text-to-speech for question
    if use_voice:
        col_voice1, col_voice2 = st.columns([1, 4])
        with col_voice1:
            if st.button("🔊 Listen", key=f"tts_{current_idx}"):
                with st.spinner("🎙️ Generating audio..."):
                    audio_bytes = Utils.text_to_speech(current_q['question'])
                    if audio_bytes:
                        st.audio(audio_bytes, format='audio/mp3')
                    else:
                        st.warning("Text-to-speech not available. Install gTTS.")
    
    # Expected points (collapsible)
    with st.expander("🎯 Expected Answer Points"):
        if current_q.get('expected_answer_points'):
            for i, point in enumerate(current_q['expected_answer_points'], 1):
                st.write(f"{i}. {point}")
        else:
            st.write("No specific points provided")
    
    # Context hint
    if current_q.get('context'):
        st.info(f"💡 **Context**: {current_q['context']}")
    
    st.markdown("---")
    
    # Answer input section
    st.subheader("✍️ Your Answer")
    
    # Check if answer already exists (for navigation back)
    existing_answer = ""
    if current_idx < len(st.session_state.answers):
        existing_answer = st.session_state.answers[current_idx]
        if existing_answer == "[Skipped]":
            existing_answer = ""
    
    # Answer input with tabs
    if use_voice:
        tab1, tab2 = st.tabs(["✏️ Type Answer", "🎤 Voice Answer"])
    else:
        tab1, tab2 = st.tabs(["✏️ Type Answer", "🎤 Voice (Not Available)"])
    
    with tab1:
        answer_key = f"answer_{current_idx}"
        answer = st.text_area(
            "Your Answer:",
            value=existing_answer,
            height=250,
            key=answer_key,
            placeholder="""Write your answer here...

Tips:
- Use specific examples from your experience
- Explain your approach step-by-step
- Mention the results or impact
- Be honest and authentic

Minimum length: """ + str(CONFIG.min_answer_length) + """ characters""",
            help=f"Minimum {CONFIG.min_answer_length} characters"
        )
        
        # Character count with color coding
        char_count = len(answer) if answer else 0
        if char_count >= CONFIG.min_answer_length:
            color = "green"
            status = "✅ Good length"
        elif char_count >= CONFIG.min_answer_length * 0.7:
            color = "orange"
            status = "⚠️ Almost there"
        else:
            color = "red"
            status = "❌ Too short"
        
        col_count1, col_count2 = st.columns([3, 1])
        with col_count2:
            st.markdown(
                f"<p style='text-align: right; color: {color}; font-weight: bold;'>"
                f"{char_count} / {CONFIG.min_answer_length} chars<br>{status}</p>", 
                unsafe_allow_html=True
            )
    
    with tab2:
        st.info("🎙️ **Voice Recording Feature**")
        st.write("This feature allows you to record your answer using voice.")
        
        try:
            audio_value = st.audio_input("Record your answer", key=f"audio_{current_idx}")
            if audio_value:
                st.success("✅ Audio recorded!")
                st.info("💡 Transcription feature coming soon. Please also type your answer.")
        except AttributeError:
            st.warning("⚠️ Audio input not available in this Streamlit version.")
            st.write("**Planned features:**")
            st.write("- 🎙️ Direct audio recording")
            st.write("- 📤 Upload audio file")
            st.write("- 🔄 Auto transcription with Whisper AI")
        
        if not use_voice:
            st.code("pip install gTTS SpeechRecognition", language="bash")
    
    st.markdown("---")
    
    # Timer warning
    if use_timer:
        question_time = time.time() - st.session_state.question_start_time
        if question_time > CONFIG.time_limit_per_question * 0.8:
            st.warning(f"⏰ Time warning: You've been on this question for {int(question_time)} seconds")
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=(current_idx == 0), use_container_width=True):
            st.session_state.current_question_idx -= 1
            st.session_state.question_start_time = time.time()
            st.rerun()
    
    with col2:
        if st.button("💾 Save Draft", use_container_width=True):
            if answer:
                # Save to session state without moving
                if len(st.session_state.answers) <= current_idx:
                    st.session_state.answers.append(answer)
                else:
                    st.session_state.answers[current_idx] = answer
                st.success("Draft saved!")
            else:
                st.warning("Nothing to save")
    
    with col3:
        if st.button("⏭️ Skip", use_container_width=True):
            # Save as skipped
            if len(st.session_state.answers) <= current_idx:
                st.session_state.answers.append("[Skipped]")
                st.session_state.answer_metadata.append({
                    'response_time': 0,
                    'skipped': True
                })
            else:
                st.session_state.answers[current_idx] = "[Skipped]"
                if len(st.session_state.answer_metadata) <= current_idx:
                    st.session_state.answer_metadata.append({
                        'response_time': 0,
                        'skipped': True
                    })
                else:
                    st.session_state.answer_metadata[current_idx] = {
                        'response_time': 0,
                        'skipped': True
                    }
            
            st.session_state.current_question_idx += 1
            st.session_state.question_start_time = time.time()
            
            if st.session_state.current_question_idx >= total_questions:
                st.session_state.stage = 'results'
            
            st.rerun()
    
    with col4:
        if st.button("Next ➡️", type="primary", use_container_width=True):
            if not answer or answer.strip() == "":
                st.error("⚠️ Please provide an answer or skip this question!")
            elif len(answer) < CONFIG.min_answer_length:
                st.error(f"⚠️ Answer too short! Minimum {CONFIG.min_answer_length} characters required.")
                st.info(f"Current length: {len(answer)} characters")
            else:
                # Calculate response time
                if st.session_state.get('question_start_time'):
                    response_time = int(time.time() - st.session_state.question_start_time)
                else:
                    response_time = 0
                
                # Save answer and metadata
                if len(st.session_state.answers) <= current_idx:
                    st.session_state.answers.append(answer)
                    st.session_state.answer_metadata.append({
                        'response_time': response_time,
                        'skipped': False
                    })
                else:
                    st.session_state.answers[current_idx] = answer
                    if len(st.session_state.answer_metadata) <= current_idx:
                        st.session_state.answer_metadata.append({
                            'response_time': response_time,
                            'skipped': False
                        })
                    else:
                        st.session_state.answer_metadata[current_idx] = {
                            'response_time': response_time,
                            'skipped': False
                        }
                
                st.session_state.current_question_idx += 1
                st.session_state.question_start_time = time.time()
                
                if st.session_state.current_question_idx >= total_questions:
                    st.session_state.stage = 'results'
                
                st.success("✅ Answer saved!")
                time.sleep(0.5)
                st.rerun()
    
    # Bottom tips
    st.markdown("---")
    with st.expander("💡 Interview Tips"):
        st.markdown("""
        **STAR Method:**
        - **S**ituation: Set the context
        - **T**ask: Describe the challenge
        - **A**ction: Explain what you did
        - **R**esult: Share the outcome
        
        **Good Answer Characteristics:**
        - Specific and detailed
        - Uses concrete examples
        - Shows your thought process
        - Demonstrates impact
        - Honest and authentic
        
        **Avoid:**
        - Generic responses
        - Too short answers
        - Lying or exaggerating
        - Negative talk about others
        """)