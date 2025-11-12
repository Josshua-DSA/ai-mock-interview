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
        
        # Save results
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
    
    # Display results using components
    render_score_metrics(scores, avg_score, passed)
    
    # Visualizations
    st.plotly_chart(
        VisualizationService.create_radar_chart(scores),
        use_container_width=True
    )
    
    st.plotly_chart(
        VisualizationService.create_bar_chart(scores),
        use_container_width=True
    )
    
    # Detailed feedback
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

            # MASIH BELUM TERDEVELOP