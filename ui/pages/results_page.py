import streamlit as st
import time
import json
from services.visualization_service import VisualizationService
from utils.helpers import Utils
from config.settings import CONFIG


def render_score_metrics(scores, avg_score, passed):
    """Display score metrics (average score, pass/fail)"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Score", f"{avg_score:.1f}", delta="vs Benchmark")
    
    with col2:
        st.metric("Passed", "✅" if passed else "❌", help="Interview Pass/Fail")
    
    with col3:
        st.metric("Questions Answered", len(st.session_state.answers))


def render_feedback_section(evaluation):
    """Render detailed feedback section"""
    st.subheader("🔍 Detailed Feedback")
    st.write(f"**Overall Assessment**: {evaluation['overall_assessment']}")
    
    st.markdown("### Strengths")
    for strength in evaluation.get('strengths', []):
        st.write(f"- {strength}")
    
    st.markdown("### Areas for Improvement")
    for improvement in evaluation.get('improvements', []):
        st.write(f"- {improvement}")
    
    st.markdown("### Missing Points")
    for point in evaluation.get('missing_points', []):
        st.write(f"- {point}")
    
    st.markdown("### Example of Better Answer")
    st.write(f"{evaluation.get('better_answer_example', 'No example provided.')}")


def show_results_page(db, llm):
    st.header("📊 Interview Results")

    with st.spinner("🔄 Evaluating..."):
        # Evaluate interview
        evaluation = llm.evaluate_full_interview(
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.cv_text,
            st.session_state.target_job
        )

        scores = evaluation['scores']
        avg_score = sum(scores.values()) / len(scores)
        passed = avg_score >= CONFIG.passing_score

        # Save results to the database
        result_data = {
            'job_title': st.session_state.target_job,
            'difficulty': st.session_state.difficulty,
            'scores': scores,
            'duration': int(time.time() - st.session_state.interview_start_time),
            'questions_answered': len(st.session_state.answers),
            'detailed_feedback': json.dumps(evaluation)
        }

        db.save_interview_result(
            st.session_state.session_id,
            st.session_state.user_id,
            result_data
        )

    # Display the metrics and scores
    render_score_metrics(scores, avg_score, passed)

    # Visualizations for the results
    st.plotly_chart(
        VisualizationService.create_radar_chart(scores),
        use_container_width=True
    )

    st.plotly_chart(
        VisualizationService.create_bar_chart(scores),
        use_container_width=True
    )

    # Detailed feedback from the evaluation
    render_feedback_section(evaluation)

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 New Interview"):
            st.session_state.stage = 'input'
            st.rerun()

    with col2:
        if st.button("📊 Analytics"):
            st.session_state.stage = 'analytics'
            st.rerun()

    with col3:
        # Export the data as JSON for download
        export_data = {
            'session_id': st.session_state.session_id,
            'scores': scores,
            'evaluation': evaluation
        }
        json_str = Utils.export_to_json(export_data)
        if json_str:
            st.download_button(
                "📥 Download",
                json_str,
                file_name=f"report_{st.session_state.session_id}.json"
            )
