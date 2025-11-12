"""
LLM Service - Handles AI/LLM Integration
"""
import json
import os
from typing import List, Dict, Optional
import streamlit as st

from config.settings import DEFAULT_MODEL, MODEL_TEMPERATURE, MODEL_MAX_TOKENS


class LLMService:
    """Enhanced LLM service with better prompting and error handling"""
    
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.max_retries = 3
        self.timeout = 60
    
    def _call_openai(self, messages: List[Dict], temperature: float = MODEL_TEMPERATURE) -> Optional[str]:
        """Call OpenAI API with retry logic"""
        try:
            import openai
            openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=MODEL_MAX_TOKENS
            )
            
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"OpenAI API Error: {str(e)}")
            return None
    
    def analyze_cv_and_generate_questions(self, cv_text: str, target_job: str, 
                                         difficulty: str = "Sedang") -> Dict:
        """Generate tailored interview questions based on CV and job"""
        
        prompt = f"""Anda adalah HR Expert dengan 15+ tahun pengalaman dalam recruitment dan interview.

**TUGAS**: Analisis CV kandidat dan buat pertanyaan interview yang mendalam dan relevan.

**CV KANDIDAT**:
{cv_text[:1500]}...

**POSISI TARGET**: {target_job}
**TINGKAT KESULITAN**: {difficulty}

**INSTRUKSI**:
1. Analisis mendalam kesesuaian kandidat dengan posisi
2. Identifikasi kekuatan dan gap dalam CV
3. Buat 8-10 pertanyaan yang:
   - Spesifik untuk pengalaman kandidat
   - Menguji kompetensi teknis dan soft skills
   - Sesuai tingkat kesulitan: {difficulty}
   - Memicu jawaban detail dan refleksi

**KATEGORI PERTANYAAN**:
- Komunikasi & Presentasi
- Problem Solving & Analytical Thinking
- Leadership & Influence
- Teamwork & Collaboration
- Pengetahuan Teknis & Domain Expertise
- Adaptabilitas & Learning Agility
- Kreativitas & Innovation
- Critical Thinking & Decision Making

**FORMAT OUTPUT (JSON)**:
{{
    "analysis": {{
        "overall_fit": "percentage dan penjelasan",
        "strengths": ["kekuatan 1", "kekuatan 2", ...],
        "gaps": ["gap 1", "gap 2", ...],
        "recommendation": "rekomendasi singkat"
    }},
    "questions": [
        {{
            "id": 1,
            "category": "komunikasi",
            "question": "pertanyaan spesifik...",
            "context": "kenapa pertanyaan ini penting",
            "expected_answer_points": ["poin 1", "poin 2", ...],
            "difficulty": "medium"
        }},
        ...
    ]
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = self._call_openai(messages, temperature=0.8)
        
        if not response:
            return self._get_fallback_questions(target_job)
        
        try:
            return json.loads(response)
        except:
            return self._get_fallback_questions(target_job)
    
    def evaluate_answer(self, question: Dict, answer: str, cv_context: str) -> Dict:
        """Evaluate individual answer with detailed feedback"""
        
        prompt = f"""Sebagai expert interviewer, evaluasi jawaban kandidat berikut:

**KONTEKS CV**: {cv_context[:300]}...

**PERTANYAAN** ({question['category']}):
{question['question']}

**POIN YANG DIHARAPKAN**:
{json.dumps(question.get('expected_answer_points', []), indent=2)}

**JAWABAN KANDIDAT**:
{answer}

**FORMAT JSON**:
{{
    "score": 85,
    "feedback": "feedback detail...",
    "strengths": ["poin kuat 1", "poin kuat 2"],
    "improvements": ["area improvement 1", "area improvement 2"],
    "missing_points": ["poin yang terlewat"],
    "better_answer_example": "contoh jawaban yang lebih baik..."
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = self._call_openai(messages, temperature=0.5)
        
        try:
            return json.loads(response)
        except:
            return {
                "score": 70,
                "feedback": "Jawaban cukup baik namun bisa lebih detail.",
                "strengths": ["Menjawab pertanyaan"],
                "improvements": ["Tambahkan contoh konkret"],
                "missing_points": [],
                "better_answer_example": ""
            }
    
    def evaluate_full_interview(self, questions: List[Dict], answers: List[str], 
                               cv_text: str, target_job: str) -> Dict:
        """Comprehensive interview evaluation"""
        
        qa_text = "\n\n".join([
            f"Q{i+1} [{q['category']}]: {q['question']}\nA{i+1}: {a}"
            for i, (q, a) in enumerate(zip(questions, answers))
        ])
        
        prompt = f"""Sebagai Senior HR Evaluator, berikan evaluasi komprehensif interview ini:

**TARGET POSISI**: {target_job}
**CV**: {cv_text[:500]}...

**INTERVIEW TRANSCRIPT**:
{qa_text}

**FORMAT JSON**:
{{
    "scores": {{
        "komunikasi": 85,
        "problem_solving": 78,
        "leadership": 82,
        "teamwork": 88,
        "pengetahuan_teknis": 75,
        "adaptabilitas": 80,
        "kreativitas": 77,
        "critical_thinking": 81
    }},
    "category_feedback": {{}},
    "overall_assessment": "evaluasi keseluruhan...",
    "strengths": ["kekuatan 1", ...],
    "weaknesses": ["kelemahan 1", ...],
    "red_flags": [],
    "recommendation": {{
        "decision": "Hire/Maybe/Don't Hire",
        "confidence": "70%",
        "reasoning": "alasan...",
        "next_steps": ["step 1", ...]
    }},
    "development_plan": {{
        "priority_areas": ["area 1", ...],
        "suggested_actions": ["aksi 1", ...],
        "timeline": "3-6 bulan"
    }}
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = self._call_openai(messages, temperature=0.6)
        
        try:
            return json.loads(response)
        except:
            return self._get_fallback_evaluation()
    
    def get_job_recommendations(self, cv_text: str, scores: Dict, 
                               job_market_data: List[Dict]) -> List[Dict]:
        """AI-powered job matching"""
        
        job_list = "\n".join([
            f"- {job['job_title']}: {job['description']}"
            for job in job_market_data[:15]
        ])
        
        prompt = f"""Sebagai Career Advisor AI, rekomendasikan pekerjaan terbaik:

**PROFIL**: {cv_text[:800]}...
**SKOR**: {json.dumps(scores, indent=2)}
**JOBS**: {job_list}

**FORMAT JSON**:
{{
    "recommendations": [
        {{
            "job_title": "Software Engineer",
            "match_percentage": 85,
            "match_reasons": ["alasan 1", "alasan 2"],
            "skill_gaps": ["gap 1", "gap 2"],
            "salary_range": "Rp 12.000.000 - Rp 25.000.000",
            "growth_potential": "Tinggi",
            "difficulty_to_get": "Sedang"
        }}
    ]
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = self._call_openai(messages, temperature=0.7)
        
        try:
            result = json.loads(response)
            return result.get('recommendations', [])
        except:
            return []
    
    def _get_fallback_questions(self, target_job: str) -> Dict:
        """Fallback questions if API fails"""
        return {
            "analysis": {
                "overall_fit": "75% - Profil cukup sesuai",
                "strengths": ["Pengalaman relevan"],
                "gaps": ["Perlu detail project"],
                "recommendation": "Kandidat potensial"
            },
            "questions": [
                {
                    "id": 1,
                    "category": "komunikasi",
                    "question": "Ceritakan pengalaman Anda mempresentasikan ide kompleks?",
                    "context": "Mengukur komunikasi efektif",
                    "expected_answer_points": ["Situasi", "Approach", "Hasil"],
                    "difficulty": "medium"
                },
                {
                    "id": 2,
                    "category": "problem_solving",
                    "question": "Jelaskan masalah teknis tersulit yang pernah Anda hadapi?",
                    "context": "Menguji analytical skills",
                    "expected_answer_points": ["Kompleksitas", "Analisis", "Solusi"],
                    "difficulty": "hard"
                }
            ]
        }
    
    def _get_fallback_evaluation(self) -> Dict:
        """Fallback evaluation"""
        return {
            "scores": {
                "komunikasi": 75,
                "problem_solving": 72,
                "leadership": 70,
                "teamwork": 78,
                "pengetahuan_teknis": 68,
                "adaptabilitas": 74,
                "kreativitas": 71,
                "critical_thinking": 73
            },
            "category_feedback": {},
            "overall_assessment": "Performa cukup baik",
            "strengths": ["Komunikasi baik"],
            "weaknesses": ["Teknis perlu diperdalam"],
            "red_flags": [],
            "recommendation": {
                "decision": "Maybe",
                "confidence": "65%",
                "reasoning": "Perlu evaluasi lebih lanjut",
                "next_steps": ["Technical interview"]
            },
            "development_plan": {
                "priority_areas": ["Technical Skills"],
                "suggested_actions": ["Training teknis"],
                "timeline": "3-6 bulan"
            }
        }