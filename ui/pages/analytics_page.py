"""
Analytics Page - Comprehensive Analytics Dashboard with Advanced Insights
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import dari utils yang sudah dipecah
from utils.timer import format_duration, calculate_grade
from utils.exporter import export_to_json

# Import services
from services.visualizations_service import VisualizationService
from config.settings import CONFIG
import json


def show_analytics_page(db):
    """Enhanced analytics dashboard with comprehensive insights and predictions"""
    st.header("📈 Analytics Dashboard")
    
    # Get analytics data
    analytics = db.get_analytics_data(st.session_state.user_id)
    history = db.get_user_history(st.session_state.user_id, limit=100)
    
    if analytics['total_interviews'] == 0:
        # Empty state
        st.info("📊 No analytics data yet. Complete some interviews to see your progress!")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Start First Interview", type="primary", use_container_width=True):
                st.session_state.stage = 'input'
                st.rerun()
        
        # Show sample analytics
        with st.expander("👀 Preview: What You'll See Here"):
            st.image("https://via.placeholder.com/800x400/667eea/ffffff?text=Analytics+Dashboard+Preview", 
                    use_container_width=True)
            st.markdown("""
            **After completing interviews, you'll see:**
            - 📊 Performance trends over time
            - 🎯 Strengths and weaknesses analysis
            - 📈 Improvement rate tracking
            - 💡 Personalized recommendations
            - 🎓 Custom learning path
            - 📉 Detailed score breakdowns
            """)
        return
    
    # KPI Section
    st.subheader("🎯 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Interviews", 
            analytics['total_interviews'],
            help="Total number of completed interviews"
        )
    
    with col2:
        avg_score = analytics['avg_score']
        st.metric(
            "Average Score", 
            f"{avg_score:.1f}",
            delta=f"{avg_score - 75:.1f} vs benchmark",
            help="Your average score across all interviews"
        )
    
    with col3:
        improvement = analytics['improvement_rate']
        st.metric(
            "Improvement",
            f"{abs(improvement):.1f}%",
            delta=f"{improvement:+.1f}%",
            delta_color="normal" if improvement >= 0 else "inverse",
            help="Your improvement from first to latest interview"
        )
    
    with col4:
        grade = calculate_grade(analytics['avg_score'])
        st.metric(
            "Grade", 
            grade.split('(')[0].strip(),
            help="Letter grade based on average score"
        )
    
    with col5:
        pass_count = sum(1 for h in history if h['pass_status'])
        pass_rate = (pass_count / len(history) * 100) if history else 0
        st.metric(
            "Pass Rate",
            f"{pass_rate:.0f}%",
            delta=f"{pass_count}/{len(history)}",
            help="Percentage of interviews passed"
        )
    
    st.markdown("---")
    
    # Quick Insights Banner
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Performance status
        if analytics['avg_score'] >= 90:
            st.success("🌟 **Outstanding Performance!** You're in the top tier!")
        elif analytics['avg_score'] >= 80:
            st.success("✨ **Excellent Performance!** Keep up the great work!")
        elif analytics['avg_score'] >= 70:
            st.info("👍 **Good Performance!** You're on the right track!")
        elif analytics['avg_score'] >= 60:
            st.warning("📚 **Fair Performance.** More practice recommended.")
        else:
            st.error("💪 **Needs Improvement.** Let's work on building your skills!")
    
    with col2:
        # Trend indicator
        if improvement > 10:
            st.success("📈 **Rising Star**")
        elif improvement > 0:
            st.info("➡️ **Steady Progress**")
        elif improvement > -10:
            st.warning("📉 **Slight Decline**")
        else:
            st.error("⚠️ **Needs Attention**")
    
    st.markdown("---")
    
    # Tab Navigation for Different Analytics
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "📈 Trends", 
        "🎯 Skills", 
        "💼 Jobs", 
        "🎓 Learning"
    ])
    
    # ==================== TAB 1: OVERVIEW ====================
    with tab1:
        st.subheader("📊 Performance Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Strengths and Weaknesses
            st.markdown("### 💪 Strengths & Weaknesses")
            
            strongest = analytics['strongest_area']
            weakest = analytics['weakest_area']
            
            # Strongest area
            st.success(f"**🌟 Strongest: {strongest[0]}**")
            st.metric("Score", f"{strongest[1]:.1f}/100")
            st.progress(strongest[1] / 100)
            
            if strongest[1] >= 90:
                st.write("🎉 Exceptional! You've mastered this area.")
            elif strongest[1] >= 80:
                st.write("👍 Very strong performance here!")
            else:
                st.write("✓ This is your relative strength.")
            
            st.markdown("---")
            
            # Weakest area
            st.warning(f"**📚 Area to Improve: {weakest[0]}**")
            st.metric("Score", f"{weakest[1]:.1f}/100")
            st.progress(weakest[1] / 100)
            
            improvement_needed = 75 - weakest[1]
            if improvement_needed > 0:
                st.write(f"📈 Need {improvement_needed:.0f} points to reach benchmark!")
            else:
                st.write("✅ Above benchmark but can still improve!")
        
        with col2:
            # Category Performance Radar
            st.markdown("### 🎯 Category Performance")
            category_scores = analytics['category_scores']
            
            st.plotly_chart(
                VisualizationService.create_radar_chart(
                    category_scores,
                    "Your Performance Profile"
                ),
                use_container_width=True
            )
            
            # Score distribution
            st.markdown("### 📊 Score Distribution")
            scores_list = [h['total_score'] for h in history]
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=scores_list,
                nbinsx=10,
                marker_color='#667eea',
                opacity=0.7
            ))
            fig.add_vline(x=CONFIG.passing_score, line_dash="dash", 
                         line_color="green", annotation_text="Pass Line")
            fig.add_vline(x=analytics['avg_score'], line_dash="dash",
                         line_color="blue", annotation_text="Your Avg")
            fig.update_layout(
                xaxis_title="Score",
                yaxis_title="Frequency",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent Performance
        st.markdown("---")
        st.markdown("### 📅 Recent Performance (Last 5 Interviews)")
        
        if len(history) > 0:
            recent = history[:5]
            
            for i, record in enumerate(recent, 1):
                status = "✅ PASS" if record['pass_status'] else "❌ FAIL"
                status_color = "#10b981" if record['pass_status'] else "#ef4444"
                
                with st.expander(
                    f"#{i} - {record['job_title']} - {record['total_score']:.1f}/100 - {status}",
                    expanded=(i == 1)
                ):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Date:** {record['created_at']}")
                        st.write(f"**Status:** {status}")
                    
                    with col2:
                        st.write(f"**Score:** {record['total_score']:.1f}/100")
                        st.write(f"**Duration:** {format_duration(record['interview_duration'])}")
                    
                    with col3:
                        st.write(f"**Difficulty:** {record['difficulty_level'] or 'N/A'}")
                        st.write(f"**Questions:** {record['questions_answered']}")
                    
                    # Mini bar chart
                    mini_scores = {
                        'Comm': record['komunikasi'],
                        'PS': record['problem_solving'],
                        'Lead': record['leadership'],
                        'Team': record['teamwork'],
                        'Tech': record['pengetahuan_teknis'],
                        'Adapt': record['adaptabilitas'],
                        'Creat': record['kreativitas'],
                        'Crit': record['critical_thinking']
                    }
                    
                    fig = px.bar(
                        x=list(mini_scores.keys()),
                        y=list(mini_scores.values()),
                        color=list(mini_scores.values()),
                        color_continuous_scale='RdYlGn',
                        range_color=[0, 100]
                    )
                    fig.update_layout(
                        height=200,
                        showlegend=False,
                        xaxis_title="",
                        yaxis_title="Score",
                        yaxis=dict(range=[0, 100])
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    # ==================== TAB 2: TRENDS ====================
    with tab2:
        st.subheader("📈 Performance Trends")
        
        if len(history) > 1:
            # Progress Timeline
            st.markdown("### 📅 Score Progress Over Time")
            st.plotly_chart(
                VisualizationService.create_progress_timeline(history),
                use_container_width=True
            )
            
            # Trend Analysis
            st.markdown("### 🔍 Trend Analysis")
            
            # Calculate rolling average
            scores = [h['total_score'] for h in reversed(history)]
            dates = [h['created_at'] for h in reversed(history)]
            
            df = pd.DataFrame({'Date': dates, 'Score': scores})
            
            if len(scores) >= 3:
                df['Rolling_Avg'] = df['Score'].rolling(window=3, min_periods=1).mean()
                df['Trend'] = df['Score'].diff()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Score with rolling average
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df['Date'], y=df['Score'],
                        mode='lines+markers',
                        name='Actual Score',
                        line=dict(color='#667eea')
                    ))
                    fig.add_trace(go.Scatter(
                        x=df['Date'], y=df['Rolling_Avg'],
                        mode='lines',
                        name='3-Interview Avg',
                        line=dict(color='#10b981', dash='dash')
                    ))
                    fig.add_hline(y=CONFIG.passing_score, line_dash="dot",
                                 line_color="green", annotation_text="Pass Line")
                    fig.update_layout(
                        title="Score Trend with Moving Average",
                        height=400,
                        xaxis_title="Date",
                        yaxis_title="Score"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Interview-to-interview change
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=df['Date'][1:],
                        y=df['Trend'][1:],
                        marker_color=df['Trend'][1:].apply(
                            lambda x: '#10b981' if x >= 0 else '#ef4444'
                        )
                    ))
                    fig.update_layout(
                        title="Score Change Between Interviews",
                        height=400,
                        xaxis_title="Date",
                        yaxis_title="Point Change"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Performance by Period
            st.markdown("---")
            st.markdown("### ⏱️ Performance by Time Period")
            
            now = datetime.now()
            
            # Group by time periods
            last_week = []
            last_month = []
            last_3_months = []
            
            for h in history:
                try:
                    date = datetime.strptime(h['created_at'], '%Y-%m-%d %H:%M:%S')
                    days_ago = (now - date).days
                    
                    if days_ago <= 7:
                        last_week.append(h['total_score'])
                    if days_ago <= 30:
                        last_month.append(h['total_score'])
                    if days_ago <= 90:
                        last_3_months.append(h['total_score'])
                except:
                    pass
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if last_week:
                    avg_week = sum(last_week) / len(last_week)
                    st.metric("Last 7 Days", f"{avg_week:.1f}", 
                             delta=f"{len(last_week)} interviews")
                else:
                    st.metric("Last 7 Days", "N/A", delta="0 interviews")
            
            with col2:
                if last_month:
                    avg_month = sum(last_month) / len(last_month)
                    st.metric("Last 30 Days", f"{avg_month:.1f}",
                             delta=f"{len(last_month)} interviews")
                else:
                    st.metric("Last 30 Days", "N/A", delta="0 interviews")
            
            with col3:
                if last_3_months:
                    avg_3m = sum(last_3_months) / len(last_3_months)
                    st.metric("Last 90 Days", f"{avg_3m:.1f}",
                             delta=f"{len(last_3_months)} interviews")
                else:
                    st.metric("Last 90 Days", "N/A", delta="0 interviews")
            
            with col4:
                st.metric("All Time", f"{analytics['avg_score']:.1f}",
                         delta=f"{len(history)} interviews")
            
            # Velocity metrics
            st.markdown("---")
            st.markdown("### ⚡ Improvement Velocity")
            
            if len(history) >= 2:
                first_score = history[-1]['total_score']
                last_score = history[0]['total_score']
                
                try:
                    first_date = datetime.strptime(history[-1]['created_at'], '%Y-%m-%d %H:%M:%S')
                    last_date = datetime.strptime(history[0]['created_at'], '%Y-%m-%d %H:%M:%S')
                    days_span = (last_date - first_date).days or 1
                    
                    total_improvement = last_score - first_score
                    improvement_per_day = total_improvement / days_span
                    improvement_per_interview = total_improvement / len(history)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Total Improvement",
                            f"{total_improvement:+.1f} pts",
                            delta=f"{first_score:.1f} → {last_score:.1f}"
                        )
                    
                    with col2:
                        st.metric(
                            "Per Day",
                            f"{improvement_per_day:+.2f} pts/day",
                            delta=f"Over {days_span} days"
                        )
                    
                    with col3:
                        st.metric(
                            "Per Interview",
                            f"{improvement_per_interview:+.2f} pts",
                            delta=f"{len(history)} interviews"
                        )
                    
                    # Prediction
                    if improvement_per_interview > 0:
                        points_to_90 = 90 - last_score
                        interviews_needed = int(points_to_90 / improvement_per_interview)
                        
                        if interviews_needed > 0 and last_score < 90:
                            st.info(f"🎯 At current pace, you could reach 90+ score in approximately **{interviews_needed}** more interviews!")
                except:
                    pass
        else:
            st.info("Complete more interviews to see trend analysis.")
    
    # ==================== TAB 3: SKILLS ====================
    with tab3:
        st.subheader("🎯 Skills Analysis")
        
        category_scores = analytics['category_scores']
        
        # Category Performance
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Category Scores")
            st.plotly_chart(
                VisualizationService.create_bar_chart(
                    category_scores,
                    "Average Score by Category"
                ),
                use_container_width=True
            )
        
        with col2:
            st.markdown("### 🎯 Performance Profile")
            st.plotly_chart(
                VisualizationService.create_radar_chart(
                    category_scores,
                    "Skill Profile"
                ),
                use_container_width=True
            )
        
        # Detailed Category Table
        st.markdown("---")
        st.markdown("### 📋 Category Details")
        
        category_data = []
        for cat, score in category_scores.items():
            gap = score - 75  # benchmark
            
            if score >= 90:
                status = "🌟"
                level = "Expert"
                color = "#10b981"
            elif score >= 80:
                status = "✨"
                level = "Advanced"
                color = "#3b82f6"
            elif score >= 70:
                status = "✅"
                level = "Proficient"
                color = "#10b981"
            elif score >= 60:
                status = "⚠️"
                level = "Developing"
                color = "#f59e0b"
            else:
                status = "❌"
                level = "Needs Work"
                color = "#ef4444"
            
            category_data.append({
                'Status': status,
                'Category': cat,
                'Score': score,
                'vs Benchmark': gap,
                'Level': level,
                'Color': color
            })
        
        df_categories = pd.DataFrame(category_data)
        df_categories = df_categories.sort_values('Score', ascending=False)
        
        # Display as styled table
        for _, row in df_categories.iterrows():
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            
            with col1:
                st.markdown(f"<h2 style='text-align: center;'>{row['Status']}</h2>", 
                           unsafe_allow_html=True)
            
            with col2:
                st.write(f"**{row['Category']}**")
                st.progress(row['Score'] / 100)
            
            with col3:
                st.metric("Score", f"{row['Score']:.1f}/100")
            
            with col4:
                st.metric("vs Benchmark", 
                         f"{row['vs Benchmark']:+.1f}",
                         delta=row['Level'])
        
        # Category Evolution
        st.markdown("---")
        st.markdown("### 📈 Category Evolution Over Time")
        
        if len(history) >= 3:
            # Get category scores over time
            category_history = {cat: [] for cat in category_scores.keys()}
            dates = []
            
            for h in reversed(history):
                dates.append(h['created_at'])
                category_history['Komunikasi'].append(h['komunikasi'])
                category_history['Problem Solving'].append(h['problem_solving'])
                category_history['Leadership'].append(h['leadership'])
                category_history['Teamwork'].append(h['teamwork'])
                category_history['Pengetahuan Teknis'].append(h['pengetahuan_teknis'])
                category_history['Adaptabilitas'].append(h['adaptabilitas'])
            
            fig = go.Figure()
            
            for cat, scores in category_history.items():
                if any(s > 0 for s in scores):  # Only show if has data
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=scores,
                        mode='lines+markers',
                        name=cat
                    ))
            
            fig.update_layout(
                title="Category Scores Over Time",
                xaxis_title="Date",
                yaxis_title="Score",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete more interviews to see category evolution.")
    
    # ==================== TAB 4: JOBS ====================
    with tab4:
        st.subheader("💼 Performance by Job Title")
        
        if len(history) > 1:
            # Group by job
            job_performance = {}
            for record in history:
                job = record['job_title']
                if job not in job_performance:
                    job_performance[job] = {
                        'scores': [],
                        'attempts': 0,
                        'passed': 0,
                        'durations': [],
                        'dates': []
                    }
                job_performance[job]['scores'].append(record['total_score'])
                job_performance[job]['attempts'] += 1
                if record['pass_status']:
                    job_performance[job]['passed'] += 1
                job_performance[job]['durations'].append(record['interview_duration'])
                job_performance[job]['dates'].append(record['created_at'])
            
            # Create summary data
            job_data = []
            for job, data in job_performance.items():
                avg_score = sum(data['scores']) / len(data['scores'])
                pass_rate = (data['passed'] / data['attempts']) * 100
                avg_duration = sum(data['durations']) / len(data['durations'])
                
                job_data.append({
                    'Job Title': job,
                    'Attempts': data['attempts'],
                    'Avg Score': avg_score,
                    'Pass Rate': pass_rate,
                    'Best Score': max(data['scores']),
                    'Latest': data['scores'][0],
                    'Avg Duration': avg_duration
                })
            
            df_jobs = pd.DataFrame(job_data)
            df_jobs = df_jobs.sort_values('Avg Score', ascending=False)
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Average score by job
                fig = px.bar(
                    df_jobs,
                    x='Job Title',
                    y='Avg Score',
                    color='Pass Rate',
                    text='Attempts',
                    title='Average Score by Job',
                    color_continuous_scale='RdYlGn',
                    range_color=[0, 100]
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Pass rate by job
                fig = px.pie(
                    df_jobs,
                    values='Attempts',
                    names='Job Title',
                    title='Interview Distribution by Job',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed table
            st.markdown("---")
            st.markdown("### 📊 Detailed Job Performance")
            
            st.dataframe(
                df_jobs.style.format({
                    'Avg Score': '{:.1f}',
                    'Pass Rate': '{:.0f}%',
                    'Best Score': '{:.1f}',
                    'Latest': '{:.1f}',
                    'Avg Duration': lambda x: format_duration(int(x))
                }).background_gradient(subset=['Avg Score'], cmap='RdYlGn', vmin=0, vmax=100),
                use_container_width=True,
                hide_index=True
            )
            
            # Job-specific insights
            st.markdown("---")
            st.markdown("### 💡 Job-Specific Insights")
            
            for job, data in job_performance.items():
                with st.expander(f"📌 {job} ({data['attempts']} attempts)"):
                    col1, col2, col3 = st.columns(3)
                    
                    avg = sum(data['scores']) / len(data['scores'])
                    with col1:
                        st.metric("Average", f"{avg:.1f}")
                    with col2:
                        st.metric("Best", f"{max(data['scores']):.1f}")
                    with col3:
                        pass_rate = (data['passed'] / data['attempts']) * 100
                        st.metric("Pass Rate", f"{pass_rate:.0f}%")
                    
                    # Score progression for this job
                    if len(data['scores']) > 1:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=list(range(1, len(data['scores']) + 1)),
                            y=list(reversed(data['scores'])),
                            mode='lines+markers',
                            name='Score'
                        ))
                        fig.add_hline(y=CONFIG.passing_score, line_dash="dash",
                                     annotation_text="Pass Line")
                        fig.update_layout(
                            title=f"Score Progression for {job}",
                            xaxis_title="Attempt",
                            yaxis_title="Score",
                            height=250
                        )
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete interviews for multiple job titles to see comparisons.")
    
    # ==================== TAB 5: LEARNING PATH ====================
    with tab5:
        st.subheader("🎓 Personalized Learning Path")
        
        # AI-Powered Recommendations
        st.markdown("### 💡 Personalized Recommendations")
        
        recommendations = []
        
        # Based on improvement rate
        if analytics['improvement_rate'] < -10:
            recommendations.append({
                'priority': 'High',
                'icon': '🚨',
                'type': 'error',
                'title': 'Performance Declining Significantly',
                'message': 'Your scores have dropped by more than 10%. This needs immediate attention.',
                'actions': [
                    'Take a break and review all previous feedback',
                    'Identify patterns in your mistakes',
                    'Start with easier difficulty levels',
                    'Focus on one category at a time',
                    'Consider seeking mentorship or coaching'
                ]
            })
        elif analytics['improvement_rate'] < -5:
            recommendations.append({
                'priority': 'Medium',
                'icon': '📉',
                'type': 'warning',
                'title': 'Recent Performance Decline',
                'message': 'Your recent scores are lower than earlier ones.',
                'actions': [
                    'Review your last 3 interview feedbacks',
                    'Identify common weak points',
                    'Practice with focused questions',
                    'Revisit fundamental concepts'
                ]
            })
        elif analytics['improvement_rate'] > 15:
            recommendations.append({
                'priority': 'Low',
                'icon': '🚀',
                'type': 'success',
                'title': 'Exceptional Progress!',
                'message': 'You\'re improving rapidly! Keep this momentum going.',
                'actions': [
                    'Challenge yourself with harder difficulty',
                    'Try different job positions',
                    'Help others by sharing your strategies',
                    'Document your learning journey'
                ]
            })
        elif analytics['improvement_rate'] > 5:
            recommendations.append({
                'priority': 'Low',
                'icon': '📈',
                'type': 'success',
                'title': 'Great Progress!',
                'message': 'You\'re steadily improving. Well done!',
                'actions': [
                    'Maintain consistent practice',
                    'Gradually increase difficulty',
                    'Explore related job roles'
                ]
            })
        else:
            recommendations.append({
                'priority': 'Medium',
                'icon': '➡️',
                'type': 'info',
                'title': 'Steady Performance',
                'message': 'Your performance is stable. Time to push for improvement.',
                'actions': [
                    'Set specific score targets',
                    'Focus on weakest categories',
                    'Try different interview strategies',
                    'Increase practice frequency'
                ]
            })
        
        # Based on weakest area
        weakest = analytics['weakest_area']
        if weakest[1] < 60:
            recommendations.append({
                'priority': 'High',
                'icon': '🎯',
                'type': 'error',
                'title': f'Critical: {weakest[0]} Needs Work',
                'message': f'Your {weakest[0]} score ({weakest[1]:.1f}) is significantly below benchmark.',
                'actions': [
                    f'Dedicate 30 minutes daily to {weakest[0]} practice',
                    f'Review related materials and examples',
                    'Seek mentorship or additional resources for this category',
                ]
            })
        elif weakest[1] < 70:
            recommendations.append({
                'priority': 'Medium',
                'icon': '⚠️',
                'type': 'warning',
                'title': f'{weakest[0]} Needs Improvement',
                'message': f'Your score in {weakest[0]} is below the benchmark. Time to focus here.',
                'actions': [
                    f'Create a study plan for {weakest[0]}',
                    'Targeted practice and mock interviews for {weakest[0]}',
                    'Request feedback from peers or mentors'
                ]
            })

        # Display Recommendations
        for rec in recommendations:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"### {rec['icon']} **{rec['title']}**")
            with col2:
                st.write(f"{rec['message']}")
                for action in rec['actions']:
                    st.write(f"- {action}")
                st.markdown(f"Priority: **{rec['priority']}**")
                st.markdown("---")

        # Display Learning Resources based on categories with lowest scores
        st.markdown("### 📚 Learning Resources")
        
        if weakest[1] < 70:
            st.markdown(f"### Recommended Learning Resources for {weakest[0]}")
            st.write("Here are some resources to improve your skills in this category.")
            # Example resources - Replace with dynamic links or actual resources
            st.write("- [Category-specific book](https://example.com)")
            st.write("- [Video tutorial](https://example.com)")
            st.write("- [Practice problems](https://example.com)")

    # ==================== END OF LEARNING PATH ====================

