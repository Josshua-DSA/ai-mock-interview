import streamlit as st
from services.visualizations_service import VisualizationService
from utils.helper import Utils
from datetime import datetime


def show_history_page(db):
    """Displays the interview history page with detailed records."""
    st.header("📚 Interview History")

    # Retrieve user history from the database
    history = db.get_user_history(st.session_state.user_id, limit=50)

    # Handle empty state
    if not history:
        st.info("No history yet. Start your first interview!")
        if st.button("🚀 Start"):
            st.session_state.stage = 'input'
            st.rerun()
        return

    # Calculate summary statistics
    total = len(history)
    avg_score = sum(h['total_score'] for h in history) / total
    passed = sum(1 for h in history if h['pass_status'])
    total_duration = sum(h['interview_duration'] for h in history)
    avg_duration = total_duration / total if total > 0 else 0

    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Interviews", total)
    col2.metric("Avg Score", f"{avg_score:.1f}")
    col3.metric("Passed Interviews", passed)

    st.markdown(f"**Average Duration:** {Utils.format_duration(avg_duration)}")
    st.markdown("---")

    # Display each interview record with expanded details
    for record in history:
        status = "✅" if record['pass_status'] else "❌"

        with st.expander(f"{status} {record['job_title']} - {record['total_score']:.1f}"):
            st.write(f"**Date:** {record['created_at']}")
            st.write(f"**Duration:** {Utils.format_duration(record['interview_duration'])}")

            # Display detailed scores in categories
            scores = {
                'Communication': record['komunikasi'],
                'Problem Solving': record['problem_solving'],
                'Leadership': record['leadership'],
                'Teamwork': record['teamwork'],
                'Technical Knowledge': record['pengetahuan_teknis'],
                'Adaptability': record['adaptabilitas'],
                'Creativity': record['kreativitas'],
                'Critical Thinking': record['critical_thinking']
            }

            # Plot a bar chart for the category scores
            st.plotly_chart(
                VisualizationService.create_bar_chart(scores, "Performance by Category"),
                use_container_width=True
            )

            # Provide detailed feedback
            st.markdown("### 💬 Feedback")
            feedback = record.get('feedback', "No feedback available.")
            st.write(feedback)

            # If the interview passed, show additional notes
            if record['pass_status']:
                st.success("✅ You passed this interview!")
            else:
                st.error("❌ You did not pass this interview. Better luck next time!")

            # Display the score trend
            st.markdown("### 📉 Score Trend Over Time")
            trend_data = {
                'Score Progress': [record['komunikasi'], record['problem_solving'], 
                                   record['leadership'], record['teamwork'],
                                   record['pengetahuan_teknis'], record['adaptabilitas'],
                                   record['kreativitas'], record['critical_thinking']]
            }

            st.plotly_chart(
                VisualizationService.create_trend_chart(trend_data, "Score Trend Over Time"),
                use_container_width=True
            )

    # Option to clear history or reset for a new set of interviews
    if st.button("🧹 Clear Interview History"):
        db.clear_user_history(st.session_state.user_id)
        st.success("History cleared successfully!")
        st.rerun()

    # Option to return to the main page
    if st.button("🏠 Return to Main Page"):
        st.session_state.stage = 'input'
        st.rerun()

