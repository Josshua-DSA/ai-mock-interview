import streamlit as st
import time
from config.settings import CONFIG
from utils.timer import format_duration
from utils import audio
from ui.components import render_question_card


def show_interview_page(db, llm):
    """Tampilan interview dengan fitur kamera dan suara"""
    st.header("🎤 Wawancara Sedang Berlangsung")

    # Mendapatkan pengaturan
    gunakan_kamera = st.session_state.get('enable_camera', False)
    gunakan_suara = st.session_state.get('enable_voice', False)
    gunakan_timer = st.session_state.get('enable_timer', True)

    # Tracking progres
    total_pertanyaan = len(st.session_state.questions)
    current_idx = st.session_state.current_question_idx
    progress = (current_idx) / total_pertanyaan if total_pertanyaan > 0 else 0

    # Progress bar dan metrik
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.progress(progress)
    with col2:
        st.metric("Pertanyaan", f"{current_idx + 1}/{total_pertanyaan}")
    with col3:
        if gunakan_timer and st.session_state.interview_start_time:
            elapsed = int(time.time() - st.session_state.interview_start_time)
            st.metric("Waktu", format_duration(elapsed))
        else:
            st.metric("Waktu", "N/A")

    # Mengecek apakah wawancara selesai
    if current_idx >= total_pertanyaan:
        st.success("✅ Wawancara selesai! Beralih ke hasil...")
        time.sleep(1)
        st.session_state.stage = 'results'
        st.rerun()
        return

    current_q = st.session_state.questions[current_idx]

    # Bagian kamera
    if gunakan_kamera:
        st.markdown("---")
        col_cam1, col_cam2 = st.columns([2, 1])
        with col_cam1:
            camera_image = st.camera_input(
                "📹 Mode Wawancara Video", 
                key=f"camera_{current_idx}"
            )
            if camera_image:
                st.caption("✅ Kamera aktif - Wawancara sedang direkam")
        with col_cam2:
            st.info("""
            **📹 Tips Kamera:**
            - Lihat ke kamera
            - Pencahayaan yang baik
            - Latar belakang profesional
            - Senyum & tampil percaya diri!
            """)
        st.markdown("---")

    # Kartu pertanyaan
    render_question_card(current_q, current_idx + 1, total_pertanyaan)

    # Text-to-speech untuk pertanyaan
    if gunakan_suara:
        col_voice1, col_voice2 = st.columns([1, 4])
        with col_voice1:
            if st.button("🔊 Dengar", key=f"tts_{current_idx}"):
                with st.spinner("🎙️ Menghasilkan suara..."):
                    audio_bytes = audio.text_to_speech(current_q['question'])
                    if audio_bytes:
                        st.audio(audio_bytes, format='audio/mp3')
                    else:
                        st.warning("Text-to-speech tidak tersedia. Install gTTS.")

    # Poin jawaban yang diharapkan (collapsible)
    with st.expander("🎯 Poin Jawaban yang Diharapkan"):
        if current_q.get('expected_answer_points'):
            for i, point in enumerate(current_q['expected_answer_points'], 1):
                st.write(f"{i}. {point}")
        else:
            st.write("Tidak ada poin khusus yang diberikan")

    # Petunjuk konteks
    if current_q.get('context'):
        st.info(f"💡 **Konteks**: {current_q['context']}")

    st.markdown("---")

    # Input jawaban
    st.subheader("✍️ Jawaban Anda")

    # Mengecek apakah jawaban sudah ada (untuk navigasi kembali)
    existing_answer = ""
    if current_idx < len(st.session_state.answers):
        existing_answer = st.session_state.answers[current_idx]
        if existing_answer == "[Skipped]":
            existing_answer = ""

    # Input jawaban dengan tab
    if gunakan_suara:
        tab1, tab2 = st.tabs(["✏️ Ketik Jawaban", "🎤 Jawaban Suara"])
    else:
        tab1, tab2 = st.tabs(["✏️ Ketik Jawaban", "🎤 Suara (Tidak Tersedia)"])

    with tab1:
        answer_key = f"answer_{current_idx}"
        answer = st.text_area(
            "Jawaban Anda:",
            value=existing_answer,
            height=250,
            key=answer_key,
            placeholder="""Tulis jawaban Anda di sini...

Tips:
- Gunakan contoh spesifik dari pengalaman Anda
- Jelaskan pendekatan Anda langkah demi langkah
- Sebutkan hasil atau dampak
- Jujur dan autentik

Panjang minimal: """ + str(CONFIG.min_answer_length) + """ karakter""",
            help=f"Panjang minimal {CONFIG.min_answer_length} karakter"
        )

        # Hitung karakter dengan warna
        char_count = len(answer) if answer else 0
        if char_count >= CONFIG.min_answer_length:
            color = "green"
            status = "✅ Panjang cukup"
        elif char_count >= CONFIG.min_answer_length * 0.7:
            color = "orange"
            status = "⚠️ Hampir mencapai"
        else:
            color = "red"
            status = "❌ Terlalu pendek"

        col_count1, col_count2 = st.columns([3, 1])
        with col_count2:
            st.markdown(
                f"<p style='text-align: right; color: {color}; font-weight: bold;'>"
                f"{char_count} / {CONFIG.min_answer_length} karakter<br>{status}</p>", 
                unsafe_allow_html=True
            )

    with tab2:
        st.info("🎙️ **Fitur Perekaman Suara**")
        st.write("Fitur ini memungkinkan Anda untuk merekam jawaban menggunakan suara.")

        try:
            audio_value = st.audio_input("Rekam jawaban Anda", key=f"audio_{current_idx}")
            if audio_value:
                st.success("✅ Audio direkam!")
                st.info("💡 Fitur transkripsi akan datang segera. Harap juga ketik jawaban Anda.")
        except AttributeError:
            st.warning("⚠️ Input audio tidak tersedia di versi Streamlit ini.")
            st.write("**Fitur yang direncanakan:**")
            st.write("- 🎙️ Perekaman audio langsung")
            st.write("- 📤 Unggah file audio")
            st.write("- 🔄 Transkripsi otomatis dengan Whisper AI")

        if not gunakan_suara:
            st.code("pip install gTTS SpeechRecognition", language="bash")

    st.markdown("---")

    # Peringatan timer
    if gunakan_timer:
        question_time = time.time() - st.session_state.question_start_time
        if question_time > CONFIG.time_limit_per_question * 0.8:
            st.warning(f"⏰ Peringatan waktu: Anda sudah {int(question_time)} detik di pertanyaan ini")

    # Tombol navigasi
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if st.button("⬅️ Sebelumnya", disabled=(current_idx == 0), use_container_width=True):
            st.session_state.current_question_idx -= 1
            st.session_state.question_start_time = time.time()
            st.rerun()

    with col2:
        if st.button("💾 Simpan Draf", use_container_width=True):
            if answer:
                # Simpan ke session state tanpa bergerak ke pertanyaan berikutnya
                if len(st.session_state.answers) <= current_idx:
                    st.session_state.answers.append(answer)
                else:
                    st.session_state.answers[current_idx] = answer
                st.success("Draf disimpan!")
            else:
                st.warning("Tidak ada yang disimpan")

    with col3:
        if st.button("⏭️ Lewati", use_container_width=True):
            # Simpan sebagai dilewati
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

            if st.session_state.current_question_idx >= total_pertanyaan:
                st.session_state.stage = 'results'

            st.rerun()

    with col4:
        if st.button("Berikutnya ➡️", type="primary", use_container_width=True):
            if not answer or answer.strip() == "":
                st.error("⚠️ Harap berikan jawaban atau lewati pertanyaan ini!")
            elif len(answer) < CONFIG.min_answer_length:
                st.error(f"⚠️ Jawaban terlalu pendek! Minimal {CONFIG.min_answer_length} karakter diperlukan.")
                st.info(f"Panjang saat ini: {len(answer)} karakter")
            else:
                # Hitung waktu respon
                if st.session_state.get('question_start_time'):
                    response_time = int(time.time() - st.session_state.question_start_time)
                else:
                    response_time = 0

                # Simpan jawaban dan metadata
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

                if st.session_state.current_question_idx >= total_pertanyaan:
                    st.session_state.stage = 'results'

                st.success("✅ Jawaban disimpan!")
                time.sleep(0.5)
                st.rerun()

    # Tips di bagian bawah
    st.markdown("---")
    with st.expander("💡 Tips Wawancara"):
        st.markdown("""
        **Metode STAR:**
        - **S**ituasi: Tentukan konteks
        - **T**ugas: Deskripsikan tantangannya
        - **A**ksi: Jelaskan apa yang Anda lakukan
        - **H**asil: Bagikan hasilnya

        **Karakteristik Jawaban yang Baik:**
        - Spesifik dan detail
        - Menggunakan contoh konkret
        - Menunjukkan proses berpikir
        - Menunjukkan dampak
        - Jujur dan autentik

        **Hindari:**
        - Jawaban yang umum
        - Jawaban terlalu pendek
        - Berbohong atau melebih-lebihkan
        - Pembicaraan negatif tentang orang lain
        """)
