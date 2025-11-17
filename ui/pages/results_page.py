import streamlit as st
import time
import json
from services.visualizations_service import VisualizationService
from utils.exporter import export_to_json
from config.settings import CONFIG


def render_score_metrics(scores, avg_score, passed):
    """Menampilkan metrik skor (skor rata-rata, lulus/gagal)"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Skor", f"{avg_score:.1f}", delta="vs Benchmark")
    
    with col2:
        st.metric("Lulus", "✅" if passed else "❌", help="Status Lulus/Gagal")
    
    with col3:
        st.metric("Jumlah Pertanyaan Dijawab", len(st.session_state.answers))


def render_feedback_section(evaluation):
    """Menampilkan bagian umpan balik detail"""
    st.subheader("🔍 Umpan Balik Detail")
    st.write(f"**Penilaian Keseluruhan**: {evaluation['overall_assessment']}")
    
    st.markdown("### Kekuatan")
    for strength in evaluation.get('strengths', []):
        st.write(f"- {strength}")
    
    st.markdown("### Area untuk Peningkatan")
    for improvement in evaluation.get('improvements', []):
        st.write(f"- {improvement}")
    
    st.markdown("### Poin yang Hilang")
    for point in evaluation.get('missing_points', []):
        st.write(f"- {point}")
    
    st.markdown("### Contoh Jawaban yang Lebih Baik")
    st.write(f"{evaluation.get('better_answer_example', 'Tidak ada contoh yang diberikan.')}")


def show_results_page(db, llm):
    st.header("📊 Hasil Wawancara")

    with st.spinner("🔄 Evaluasi..."):
        # Evaluasi wawancara
        evaluation = llm.evaluate_full_interview(
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.cv_text,
            st.session_state.target_job
        )

        scores = evaluation['scores']
        avg_score = sum(scores.values()) / len(scores)
        passed = avg_score >= CONFIG.passing_score

        # Simpan hasil wawancara ke database
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

    # Menampilkan metrik dan skor
    render_score_metrics(scores, avg_score, passed)

    # Visualisasi hasil wawancara
    st.plotly_chart(
        VisualizationService.create_radar_chart(scores),
        use_container_width=True
    )

    st.plotly_chart(
        VisualizationService.create_bar_chart(scores),
        use_container_width=True
    )

    # Umpan balik detail dari evaluasi
    render_feedback_section(evaluation)

    # Tombol aksi
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Wawancara Baru"):
            st.session_state.stage = 'input'
            st.rerun()

    with col2:
        if st.button("📊 Analitik"):
            st.session_state.stage = 'analytics'
            st.rerun()

    with col3:
        # Mengekspor data sebagai file JSON untuk diunduh
        export_data = {
            'session_id': st.session_state.session_id,
            'scores': scores,
            'evaluation': evaluation
        }
        json_str = export_to_json(export_data)
        if json_str:
            st.download_button(
                "📥 Unduh",
                json_str,
                file_name=f"laporan_{st.session_state.session_id}.json"
            )
