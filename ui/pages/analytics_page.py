def show_analytics_page(db):
    st.header("📈 Analytics Dashboard")
    
    analytics = db.get_analytics_data(st.session_state.user_id)
    
    if analytics['total_interviews'] == 0:
        st.info("No data yet. Complete interviews to see analytics!")
        if st.button("🚀 Start"):
            st.session_state.stage = 'input'
            st.rerun()
        return
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Interviews", analytics['total_interviews'])
    col2.metric("Avg Score", f"{analytics['avg_score']:.1f}")
    col3.metric("Improvement", f"{analytics['improvement_rate']:+.1f}%")
    col4.metric("Grade", Utils.calculate_grade(analytics['avg_score']))
    
    st.markdown("---")
    
    # Performance analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("**🌟 Strongest**")
        strongest = analytics['strongest_area']
        st.metric(strongest[0], f"{strongest[1]:.1f}")
    
    with col2:
        st.warning("**📚 To Improve**")
        weakest = analytics['weakest_area']
        st.metric(weakest[0], f"{weakest[1]:.1f}")
    
    # Progress timeline
    history = db.get_user_history(st.session_state.user_id, limit=20)
    st.plotly_chart(
        VisualizationService.create_progress_timeline(history),
        use_container_width=True
    )
    
    # Category scores
    st.plotly_chart(
        VisualizationService.create_bar_chart(
            analytics['category_scores'],
            "Average by Category"
        ),
        use_container_width=True
    )

    # MASIH BELOM TERDEVELOP