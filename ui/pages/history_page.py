def show_history_page(db):
    st.header("📚 Interview History")
    
    history = db.get_user_history(st.session_state.user_id, limit=50)
    
    if not history:
        st.info("No history yet. Start your first interview!")
        if st.button("🚀 Start"):
            st.session_state.stage = 'input'
            st.rerun()
        return
    
    # Summary stats
    total = len(history)
    avg_score = sum(h['total_score'] for h in history) / total
    passed = sum(1 for h in history if h['pass_status'])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", total)
    col2.metric("Avg Score", f"{avg_score:.1f}")
    col3.metric("Passed", passed)
    
    st.markdown("---")
    
    # Display history
    for record in history:
        status = "✅" if record['pass_status'] else "❌"
        
        with st.expander(
            f"{status} {record['job_title']} - {record['total_score']:.1f}"
        ):
            st.write(f"Date: {record['created_at']}")
            st.write(f"Duration: {Utils.format_duration(record['interview_duration'])}")
            
            # Display scores
            scores = {
                'komunikasi': record['komunikasi'],
                'problem_solving': record['problem_solving'],
                'leadership': record['leadership'],
                'teamwork': record['teamwork']
            }
            
            st.plotly_chart(
                VisualizationService.create_bar_chart(scores),
                use_container_width=True
            )

            # MASIH BELOM TERDEVELOP