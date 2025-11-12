import plotly.graph_objects as go
from typing import Dict, List
import pandas as pd

class VisualizationService:
    """Service to create various visualizations for interview results and analytics."""

    @staticmethod
    def create_radar_chart(scores: Dict, title: str = "Interview Scores") -> go.Figure:
        """Create a radar chart to visualize interview scores across different categories."""
        categories = [k.replace('_', ' ').title() for k in scores.keys()]
        values = list(scores.values())

        # Create the radar chart figure
        fig = go.Figure()

        # User's score
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Your Score',
            line=dict(color='#3b82f6', width=2),
            fillcolor='rgba(59, 130, 246, 0.3)'
        ))

        # Benchmark score (fixed at 75 for comparison)
        avg_benchmark = [75] * len(categories)
        fig.add_trace(go.Scatterpolar(
            r=avg_benchmark,
            theta=categories,
            name='Benchmark (75)',
            line=dict(color='#10b981', width=2, dash='dash'),
            fill=None
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10),
                    gridcolor='rgba(128, 128, 128, 0.2)'
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color='#1f2937')
                )
            ),
            showlegend=True,
            title=dict(text=title, font=dict(size=16, color='#1f2937')),
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        return fig

    @staticmethod
    def create_bar_chart(scores: Dict, title: str = 'Category Breakdown') -> go.Figure:
        """Create a bar chart to show interview scores for each category."""
        categories = [k.replace('_', ' ').title() for k in scores.keys()]
        values = list(scores.values())

        # Color the bars based on the value (score range)
        colors = ['#ef4444' if v < 60 else '#f59e0b' if v < 75 else '#10b981' for v in values]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            marker=dict(
                color=colors,
                line=dict(color='rgba(0,0,0,0.3)', width=1)
            ),
            text=values,
            texttemplate='%{text:.1f}',
            textposition='outside',
            textfont=dict(size=12, color='#1f2937')
        ))

        fig.update_layout(
            title=dict(text=title, font=dict(size=16, color='#1f2937')),
            xaxis_title='Category',
            yaxis_title='Score',
            yaxis=dict(range=[0, 110]),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(tickangle=-45)
        )

        return fig

    @staticmethod
    def create_progress_timeline(user_id: str, db) -> go.Figure:
        """Create a progress timeline to show how interview scores have changed over time."""
        history = db.get_user_history(user_id, limit=20)

        if not history:
            return go.Figure()

        dates = [h['created_at'] for h in history]
        scores = [h['total_score'] for h in history]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            name='Total Score',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8, color='#3b82f6'),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.2)'
        ))

        fig.add_hline(
            y=75,
            line_dash="dash",
            line_color="#10b981",
            annotation_text="Passing Score (75)"
        )

        fig.update_layout(
            title='Progress Over Time',
            xaxis_title='Date',
            yaxis_title='Score',
            yaxis=dict(range=[0, 100]),
            height=350,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        return fig

    @staticmethod
    def create_gauge_chart(score: float, title: str = "Overall Score") -> go.Figure:
        """Create a gauge chart to display the overall score of the interview."""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 18}},
            delta={'reference': 75, 'increasing': {'color': "#10b981"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
                'bar': {'color': "#3b82f6"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 60], 'color': '#fee2e2'},
                    {'range': [60, 75], 'color': '#fef3c7'},
                    {'range': [75, 100], 'color': '#d1fae5'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 75
                }
            }
        ))

        fig.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': "#1f2937", 'family': "Arial"}
        )

        return fig

    @staticmethod
    def create_comparison_chart(current_scores: Dict, history_scores: List[Dict]) -> go.Figure:
        """Create a comparison chart to show progress between multiple interview scores."""
        if not history_scores:
            return VisualizationService.create_bar_chart(current_scores)

        categories = list(current_scores.keys())

        fig = go.Figure()

        # Add historical scores
        for i, hist in enumerate(history_scores[-3:]):  # Last 3 interviews
            fig.add_trace(go.Bar(
                name=f'Interview {len(history_scores) - len(history_scores[-3:]) + i + 1}',
                x=[k.replace('_', ' ').title() for k in categories],
                y=[hist.get(k, 0) for k in categories],
                opacity=0.6
            ))

        # Add current score
        fig.add_trace(go.Bar(
            name='Current',
            x=[k.replace('_', ' ').title() for k in categories],
            y=list(current_scores.values()),
            marker=dict(color='#3b82f6')
        ))

        fig.update_layout(
            title='Progress Comparison',
            xaxis_title='Category',
            yaxis_title='Score',
            yaxis=dict(range=[0, 100]),
            barmode='group',
            height=400,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        return fig