import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Optional, Tuple
import os
import hashlib
import re
from dataclasses import dataclass
from enum import Enum
import time
import base64
from io import BytesIO

# Optional imports with error handling
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    
try:
    from gtts import gTTS
except ImportError:
    gTTS = None

# ============================
# CONFIGURATION & CONSTANTS
# ============================

class InterviewDifficulty(Enum):
    EASY = "Mudah"
    MEDIUM = "Sedang"
    HARD = "Sulit"
    EXPERT = "Ahli"

class JobCategory(Enum):
    TECH = "Teknologi"
    MARKETING = "Marketing"
    FINANCE = "Keuangan"
    HR = "HR"
    SALES = "Penjualan"
    OPERATIONS = "Operasional"
    CREATIVE = "Kreatif"
    MANAGEMENT = "Manajemen"

@dataclass
class InterviewConfig:
    min_answer_length: int = 50
    max_questions: int = 10
    time_limit_per_question: int = 300  # 5 minutes
    passing_score: float = 70.0
    enable_voice: bool = True
    enable_analytics: bool = True

CONFIG = InterviewConfig()

# ============================
# ENHANCED DATABASE OPERATIONS
# ============================

class DatabaseManager:
    """Enhanced database manager with connection pooling and better error handling"""
    
    def __init__(self, db_path: str = 'interview_training.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with enhanced schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Enhanced user profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                email TEXT,
                full_name TEXT,
                cv_text TEXT NOT NULL,
                cv_hash TEXT,
                target_job TEXT NOT NULL,
                job_category TEXT,
                experience_years INTEGER DEFAULT 0,
                education_level TEXT,
                skills TEXT,
                preferences TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Enhanced interview results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interview_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                job_title TEXT NOT NULL,
                difficulty_level TEXT,
                komunikasi REAL DEFAULT 0,
                problem_solving REAL DEFAULT 0,
                leadership REAL DEFAULT 0,
                teamwork REAL DEFAULT 0,
                pengetahuan_teknis REAL DEFAULT 0,
                adaptabilitas REAL DEFAULT 0,
                kreativitas REAL DEFAULT 0,
                critical_thinking REAL DEFAULT 0,
                total_score REAL DEFAULT 0,
                pass_status BOOLEAN DEFAULT 0,
                interview_duration INTEGER,
                questions_answered INTEGER,
                interview_transcript TEXT,
                detailed_feedback TEXT,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
        ''')
        
        # Question-Answer history with detailed tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                question_id INTEGER,
                category TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                answer_length INTEGER,
                response_time INTEGER,
                score REAL,
                feedback TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES interview_results(session_id)
            )
        ''')
        
        # User progress tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                improvement_rate REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Job market data (mock data for recommendations)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                category TEXT,
                avg_salary_min INTEGER,
                avg_salary_max INTEGER,
                demand_level TEXT,
                required_skills TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON interview_results(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON qa_history(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON interview_results(created_at)')
        
        conn.commit()
        conn.close()
        
        # Seed initial job market data
        self.seed_job_market_data()
    
    def seed_job_market_data(self):
        """Seed initial job market data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM job_market')
        if cursor.fetchone()[0] == 0:
            jobs = [
                ("Software Engineer", "Teknologi", 12000000, 25000000, "Tinggi", 
                 "Python,Java,JavaScript,SQL,Git", "Mengembangkan dan memelihara aplikasi software"),
                ("Data Scientist", "Teknologi", 15000000, 30000000, "Sangat Tinggi",
                 "Python,R,SQL,Machine Learning,Statistics", "Analisis data dan machine learning"),
                ("Product Manager", "Manajemen", 15000000, 35000000, "Tinggi",
                 "Product Strategy,Agile,Communication,Analytics", "Mengelola lifecycle produk"),
                ("UX Designer", "Kreatif", 10000000, 20000000, "Sedang",
                 "Figma,Adobe XD,User Research,Prototyping", "Desain pengalaman pengguna"),
                ("Digital Marketing", "Marketing", 8000000, 18000000, "Tinggi",
                 "SEO,SEM,Social Media,Content Marketing,Analytics", "Strategi marketing digital"),
                ("Business Analyst", "Operasional", 10000000, 22000000, "Tinggi",
                 "SQL,Excel,Data Analysis,Business Intelligence", "Analisis bisnis dan requirements"),
                ("DevOps Engineer", "Teknologi", 14000000, 28000000, "Sangat Tinggi",
                 "Docker,Kubernetes,AWS,CI/CD,Linux", "Automation dan infrastructure"),
                ("HR Manager", "HR", 12000000, 25000000, "Sedang",
                 "Recruitment,Employee Relations,HRIS,Labor Law", "Manajemen sumber daya manusia"),
                ("Sales Manager", "Penjualan", 10000000, 30000000, "Tinggi",
                 "Negotiation,CRM,Sales Strategy,Communication", "Manajemen tim penjualan"),
                ("Financial Analyst", "Keuangan", 10000000, 22000000, "Sedang",
                 "Financial Modeling,Excel,Accounting,Analysis", "Analisis keuangan perusahaan"),
            ]
            
            cursor.executemany('''
                INSERT INTO job_market (job_title, category, avg_salary_min, avg_salary_max, 
                                       demand_level, required_skills, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', jobs)
            
            conn.commit()
        
        conn.close()
    
    def save_user_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Save or update user profile"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cv_hash = hashlib.md5(profile_data['cv_text'].encode()).hexdigest()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (user_id, email, full_name, cv_text, cv_hash, target_job, job_category, 
                 experience_years, education_level, skills, preferences, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                profile_data.get('email'),
                profile_data.get('full_name'),
                profile_data['cv_text'],
                cv_hash,
                profile_data['target_job'],
                profile_data.get('job_category'),
                profile_data.get('experience_years', 0),
                profile_data.get('education_level'),
                json.dumps(profile_data.get('skills', [])),
                json.dumps(profile_data.get('preferences', {}))
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error saving profile: {str(e)}")
            return False
    
    def save_interview_result(self, session_id: str, user_id: str, result_data: Dict) -> bool:
        """Save interview results with enhanced metrics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            scores = result_data['scores']
            total_score = sum(scores.values()) / len(scores)
            pass_status = total_score >= CONFIG.passing_score
            
            cursor.execute('''
                INSERT INTO interview_results 
                (user_id, session_id, job_title, difficulty_level, komunikasi, problem_solving, 
                 leadership, teamwork, pengetahuan_teknis, adaptabilitas, kreativitas, 
                 critical_thinking, total_score, pass_status, interview_duration, 
                 questions_answered, interview_transcript, detailed_feedback, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, session_id, result_data['job_title'], result_data.get('difficulty'),
                scores.get('komunikasi', 0), scores.get('problem_solving', 0),
                scores.get('leadership', 0), scores.get('teamwork', 0),
                scores.get('pengetahuan_teknis', 0), scores.get('adaptabilitas', 0),
                scores.get('kreativitas', 0), scores.get('critical_thinking', 0),
                total_score, pass_status, result_data.get('duration', 0),
                result_data.get('questions_answered', 0),
                result_data.get('transcript'), result_data.get('detailed_feedback'),
                result_data.get('recommendations')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error saving interview result: {str(e)}")
            return False
    
    def save_qa_pair(self, session_id: str, qa_data: Dict) -> bool:
        """Save question-answer pair with metadata"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO qa_history 
                (user_id, session_id, question_id, category, question, answer, 
                 answer_length, response_time, score, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                qa_data['user_id'], session_id, qa_data.get('question_id'),
                qa_data.get('category'), qa_data['question'], qa_data['answer'],
                len(qa_data['answer']), qa_data.get('response_time', 0),
                qa_data.get('score', 0), qa_data.get('feedback', '')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error saving Q&A: {str(e)}")
            return False
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get user interview history with rich data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM interview_results 
            WHERE user_id = ? 
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_user_progress(self, user_id: str, metric: Optional[str] = None) -> pd.DataFrame:
        """Get user progress over time"""
        conn = self.get_connection()
        
        if metric:
            query = '''
                SELECT metric_name, metric_value, improvement_rate, recorded_at
                FROM user_progress
                WHERE user_id = ? AND metric_name = ?
                ORDER BY recorded_at ASC
            '''
            df = pd.read_sql_query(query, conn, params=(user_id, metric))
        else:
            query = '''
                SELECT metric_name, metric_value, improvement_rate, recorded_at
                FROM user_progress
                WHERE user_id = ?
                ORDER BY recorded_at ASC
            '''
            df = pd.read_sql_query(query, conn, params=(user_id,))
        
        conn.close()
        return df
    
    def get_analytics_data(self, user_id: str) -> Dict:
        """Get comprehensive analytics for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get total interviews
        cursor.execute('SELECT COUNT(*) FROM interview_results WHERE user_id = ?', (user_id,))
        total_interviews = cursor.fetchone()[0]
        
        # Get average score
        cursor.execute('SELECT AVG(total_score) FROM interview_results WHERE user_id = ?', (user_id,))
        avg_score = cursor.fetchone()[0] or 0
        
        # Get improvement rate
        cursor.execute('''
            SELECT total_score, created_at 
            FROM interview_results 
            WHERE user_id = ? 
            ORDER BY created_at ASC
        ''', (user_id,))
        scores = cursor.fetchall()
        
        improvement_rate = 0
        if len(scores) >= 2:
            first_score = scores[0][0]
            last_score = scores[-1][0]
            improvement_rate = ((last_score - first_score) / first_score) * 100 if first_score > 0 else 0
        
        # Get strongest and weakest areas
        cursor.execute('''
            SELECT AVG(komunikasi) as kom, AVG(problem_solving) as ps, 
                   AVG(leadership) as lead, AVG(teamwork) as team,
                   AVG(pengetahuan_teknis) as tech, AVG(adaptabilitas) as adapt
            FROM interview_results WHERE user_id = ?
        ''', (user_id,))
        
        avgs = cursor.fetchone()
        areas = {
            'Komunikasi': avgs[0] or 0,
            'Problem Solving': avgs[1] or 0,
            'Leadership': avgs[2] or 0,
            'Teamwork': avgs[3] or 0,
            'Pengetahuan Teknis': avgs[4] or 0,
            'Adaptabilitas': avgs[5] or 0
        }
        
        strongest = max(areas.items(), key=lambda x: x[1]) if areas else ('N/A', 0)
        weakest = min(areas.items(), key=lambda x: x[1]) if areas else ('N/A', 0)
        
        conn.close()
        
        return {
            'total_interviews': total_interviews,
            'avg_score': round(avg_score, 2),
            'improvement_rate': round(improvement_rate, 2),
            'strongest_area': strongest,
            'weakest_area': weakest,
            'category_scores': areas
        }

# ============================
# AI/LLM INTEGRATION (Enhanced)
# ============================

class LLMService:
    """Enhanced LLM service with better prompting and error handling"""
    
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.max_retries = 3
        self.timeout = 60
    
    def _call_openai(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """Call OpenAI API with retry logic"""
        try:
            import openai
            openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
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
}}

**PENTING**: 
- Pertanyaan harus SANGAT spesifik untuk kandidat ini
- Hindari pertanyaan generik/template
- Gunakan bahasa Indonesia profesional
- Sesuaikan dengan industri dan level posisi"""

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

**EVALUASI**:
1. Skor (0-100): Berdasarkan relevansi, kedalaman, struktur, dan contoh konkret
2. Feedback konstruktif: Apa yang baik dan apa yang perlu diperbaiki
3. Missing points: Apa yang seharusnya dijelaskan tapi tidak disebutkan
4. Improvement tips: Saran spesifik untuk jawaban lebih baik

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
                "improvements": ["Tambahkan contoh konkret", "Jelaskan lebih detail"],
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

**EVALUASI KOMPREHENSIF**:

1. **SCORING** (0-100 untuk setiap kategori):
   - Komunikasi: Kejelasan, struktur, artikulasi
   - Problem Solving: Analytical thinking, approach sistematis
   - Leadership: Initiative, influence, decision making
   - Teamwork: Collaboration, interpersonal skills
   - Pengetahuan Teknis: Domain knowledge, expertise
   - Adaptabilitas: Flexibility, learning agility
   - Kreativitas: Innovation, out-of-box thinking
   - Critical Thinking: Analysis depth, logical reasoning

2. **ANALISIS MENDALAM**:
   - Overall performance assessment
   - Interview flow quality
   - Consistency dengan CV
   - Red flags (jika ada)

3. **REKOMENDASI**:
   - Hire/Don't Hire/Maybe dengan reasoning
   - Next steps yang disarankan
   - Development areas prioritas

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
    "category_feedback": {{
        "komunikasi": "feedback spesifik...",
        "problem_solving": "feedback spesifik...",
        "leadership": "feedback spesifik...",
        "teamwork": "feedback spesifik...",
        "pengetahuan_teknis": "feedback spesifik...",
        "adaptabilitas": "feedback spesifik...",
        "kreativitas": "feedback spesifik...",
        "critical_thinking": "feedback spesifik..."
    }},
    "overall_assessment": "evaluasi keseluruhan...",
    "strengths": ["kekuatan utama 1", "kekuatan utama 2", ...],
    "weaknesses": ["kelemahan yang perlu diperbaiki", ...],
    "red_flags": ["concern jika ada"],
    "recommendation": {{
        "decision": "Hire/Don't Hire/Maybe",
        "confidence": "70%",
        "reasoning": "alasan keputusan...",
        "next_steps": ["langkah 1", "langkah 2"]
    }},
    "development_plan": {{
        "priority_areas": ["area 1", "area 2"],
        "suggested_actions": ["aksi 1", "aksi 2"],
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
        """AI-powered job matching and recommendations"""
        
        job_list = "\n".join([
            f"- {job['job_title']}: {job['description']} (Skills: {job['required_skills']})"
            for job in job_market_data[:15]
        ])
        
        prompt = f"""Sebagai Career Advisor AI, analisis profil kandidat dan rekomendasikan pekerjaan terbaik:

**PROFIL KANDIDAT**:
CV: {cv_text[:800]}...

**SKOR INTERVIEW**:
{json.dumps(scores, indent=2)}

**AVAILABLE JOBS**:
{job_list}

**TUGAS**:
1. Analisis kesesuaian kandidat dengan setiap pekerjaan
2. Rekomendasikan 5-7 pekerjaan terbaik dengan match percentage
3. Jelaskan mengapa cocok dan skill gap yang perlu ditutup
4. Berikan career path suggestions

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
        }},
        ...
    ],
    "career_path": {{
        "short_term": "posisi entry/mid level",
        "mid_term": "posisi setelah 2-3 tahun",
        "long_term": "posisi ideal 5+ tahun"
    }},
    "skill_development": {{
        "must_have": ["skill critical 1", ...],
        "nice_to_have": ["skill bonus", ...],
        "learning_resources": ["resource 1", ...]
    }}
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
                "overall_fit": "75% - Profil cukup sesuai dengan posisi",
                "strengths": ["Pengalaman relevan", "Skill set memadai"],
                "gaps": ["Perlu lebih detail tentang project specific"],
                "recommendation": "Kandidat potensial untuk dipertimbangkan"
            },
            "questions": [
                {
                    "id": 1,
                    "category": "komunikasi",
                    "question": "Ceritakan pengalaman Anda dalam mempresentasikan ide kompleks kepada stakeholder non-teknis?",
                    "context": "Mengukur kemampuan komunikasi efektif",
                    "expected_answer_points": ["Situasi spesifik", "Approach yang digunakan", "Hasil"],
                    "difficulty": "medium"
                },
                {
                    "id": 2,
                    "category": "problem_solving",
                    "question": "Jelaskan masalah teknis tersulit yang pernah Anda hadapi dan bagaimana Anda menyelesaikannya?",
                    "context": "Menguji analytical dan problem-solving skills",
                    "expected_answer_points": ["Kompleksitas masalah", "Proses analisis", "Solusi", "Learning"],
                    "difficulty": "hard"
                },
                {
                    "id": 3,
                    "category": "leadership",
                    "question": f"Untuk posisi {target_job}, bagaimana Anda akan memimpin tim dalam menghadapi deadline ketat?",
                    "context": "Menguji leadership style dan pressure handling",
                    "expected_answer_points": ["Leadership approach", "Prioritization", "Team motivation"],
                    "difficulty": "medium"
                },
                {
                    "id": 4,
                    "category": "teamwork",
                    "question": "Ceritakan pengalaman ketika Anda harus bekerja dengan rekan tim yang sulit. Bagaimana Anda menanganinya?",
                    "context": "Mengukur interpersonal skills dan conflict resolution",
                    "expected_answer_points": ["Situasi", "Approach", "Resolusi", "Learning"],
                    "difficulty": "medium"
                },
                {
                    "id": 5,
                    "category": "pengetahuan_teknis",
                    "question": f"Jelaskan teknologi atau metodologi terkini yang relevan untuk posisi {target_job}. Bagaimana Anda mengimplementasikannya?",
                    "context": "Menguji technical knowledge dan up-to-date awareness",
                    "expected_answer_points": ["Technology understanding", "Implementation experience", "Best practices"],
                    "difficulty": "hard"
                },
                {
                    "id": 6,
                    "category": "adaptabilitas",
                    "question": "Ceritakan situasi ketika Anda harus belajar skill baru dengan cepat. Apa strategi Anda?",
                    "context": "Mengukur learning agility",
                    "expected_answer_points": ["Learning approach", "Resources used", "Application", "Outcome"],
                    "difficulty": "medium"
                },
                {
                    "id": 7,
                    "category": "kreativitas",
                    "question": "Jelaskan ide inovatif yang pernah Anda usulkan atau implementasikan. Apa impact-nya?",
                    "context": "Menguji creative thinking dan innovation",
                    "expected_answer_points": ["Ide", "Implementation", "Challenges", "Impact"],
                    "difficulty": "medium"
                },
                {
                    "id": 8,
                    "category": "critical_thinking",
                    "question": "Bagaimana Anda membuat keputusan penting ketika data yang tersedia terbatas atau ambigu?",
                    "context": "Menguji decision making under uncertainty",
                    "expected_answer_points": ["Decision framework", "Risk assessment", "Validation", "Learning"],
                    "difficulty": "hard"
                }
            ]
        }
    
    def _get_fallback_evaluation(self) -> Dict:
        """Fallback evaluation if API fails"""
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
            "category_feedback": {
                "komunikasi": "Komunikasi cukup jelas, perlu lebih terstruktur",
                "problem_solving": "Menunjukkan kemampuan analitis yang baik",
                "leadership": "Potensi leadership terlihat, perlu lebih banyak contoh",
                "teamwork": "Kemampuan kolaborasi sangat baik",
                "pengetahuan_teknis": "Perlu memperdalam pengetahuan teknis",
                "adaptabilitas": "Menunjukkan fleksibilitas yang memadai",
                "kreativitas": "Ide-ide cukup inovatif",
                "critical_thinking": "Analytical thinking cukup baik"
            },
            "overall_assessment": "Kandidat menunjukkan performa yang cukup baik dengan potensi untuk berkembang. Beberapa area memerlukan peningkatan.",
            "strengths": ["Komunikasi yang baik", "Kemampuan teamwork", "Adaptabilitas"],
            "weaknesses": ["Pengetahuan teknis perlu diperdalam", "Leadership presence bisa lebih kuat"],
            "red_flags": [],
            "recommendation": {
                "decision": "Maybe",
                "confidence": "65%",
                "reasoning": "Kandidat potensial namun perlu evaluasi lebih lanjut pada aspek teknis",
                "next_steps": ["Technical deep-dive", "Meet the team", "Case study"]
            },
            "development_plan": {
                "priority_areas": ["Pengetahuan Teknis", "Leadership Skills"],
                "suggested_actions": [
                    "Ikuti training/sertifikasi teknis",
                    "Ambil leadership role dalam project",
                    "Pelajari best practices industri"
                ],
                "timeline": "3-6 bulan"
            }
        }

# ============================
# ENHANCED VISUALIZATION
# ============================

class VisualizationService:
    """Enhanced visualization with multiple chart types"""
    
    @staticmethod
    def create_radar_chart(scores: Dict, title: str = "Hasil Penilaian Interview") -> go.Figure:
        """Create enhanced radar chart"""
        categories = [k.replace('_', ' ').title() for k in scores.keys()]
        values = list(scores.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Skor Anda',
            line=dict(color='#3b82f6', width=2),
            fillcolor='rgba(59, 130, 246, 0.3)'
        ))
        
        # Add average benchmark line
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
    def create_comparison_chart(current_scores: Dict, history_scores: List[Dict]) -> go.Figure:
        """Create comparison chart showing progress"""
        if not history_scores:
            return VisualizationService.create_bar_chart(current_scores)
        
        categories = list(current_scores.keys())
        
        fig = go.Figure()
        
        # Add historical scores
        for i, hist in enumerate(history_scores[-3:]):  # Last 3 interviews
            fig.add_trace(go.Bar(
                name=f'Interview {len(history_scores)-len(history_scores[-3:])+i+1}',
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
            xaxis_title='Kategori',
            yaxis_title='Skor',
            yaxis=dict(range=[0, 100]),
            barmode='group',
            height=400,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    @staticmethod
    def create_bar_chart(scores: Dict, title: str = 'Penilaian per Kategori') -> go.Figure:
        """Create enhanced bar chart"""
        categories = [k.replace('_', ' ').title() for k in scores.keys()]
        values = list(scores.values())
        
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
            xaxis_title='Kategori',
            yaxis_title='Skor',
            yaxis=dict(range=[0, 110]),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(tickangle=-45)
        )
        
        return fig
    
    @staticmethod
    def create_progress_timeline(user_id: str, db: DatabaseManager) -> go.Figure:
        """Create timeline of user progress"""
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
        
        # Add passing score line
        fig.add_hline(
            y=CONFIG.passing_score,
            line_dash="dash",
            line_color="#10b981",
            annotation_text=f"Passing Score ({CONFIG.passing_score})"
        )
        
        fig.update_layout(
            title='Score Progress Over Time',
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
        """Create gauge chart for overall score"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 18}},
            delta={'reference': CONFIG.passing_score, 'increasing': {'color': "#10b981"}},
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
                    'value': CONFIG.passing_score
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': "#1f2937", 'family': "Arial"}
        )
        
        return fig

# ============================
# UTILITY FUNCTIONS
# ============================

class Utils:
    """Utility functions for the application"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"session_{timestamp}_{random_hash}"
    
    @staticmethod
    def extract_text_from_pdf(pdf_file) -> Optional[str]:
        """Extract text from uploaded PDF file"""
        if PyPDF2 is None:
            st.error("❌ PyPDF2 not installed. Please install it with: pip install PyPDF2")
            return None
        
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return None
    
    @staticmethod
    def validate_cv(cv_text: str) -> Tuple[bool, str]:
        """Validate CV text"""
        if not cv_text or len(cv_text.strip()) < 100:
            return False, "CV terlalu singkat. Minimal 100 karakter."
        
        if len(cv_text) > 10000:
            return False, "CV terlalu panjang. Maksimal 10.000 karakter."
        
        # Check for basic CV elements
        cv_lower = cv_text.lower()
        has_experience = any(word in cv_lower for word in ['pengalaman', 'experience', 'kerja', 'work'])
        has_skills = any(word in cv_lower for word in ['skill', 'kemampuan', 'keahlian', 'kompeten'])
        
        if not (has_experience or has_skills):
            return False, "CV harus mencantumkan pengalaman atau keahlian."
        
        return True, "CV valid"
    
    @staticmethod
    def text_to_speech(text: str, lang: str = 'id') -> Optional[bytes]:
        """Convert text to speech"""
        if gTTS is None:
            return None
        
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            st.error(f"Error generating speech: {str(e)}")
            return None
    
    @staticmethod
    def autoplay_audio(audio_bytes: bytes):
        """Autoplay audio in browser"""
        b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in readable format"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    
    @staticmethod
    def calculate_grade(score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Very Good)"
        elif score >= 70:
            return "C (Good)"
        elif score >= 60:
            return "D (Fair)"
        else:
            return "E (Needs Improvement)"
    
    @staticmethod
    def export_to_json(data: Dict, filename: str = "interview_result.json"):
        """Export data to JSON file"""
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            return json_str
        except Exception as e:
            st.error(f"Error exporting data: {str(e)}")
            return None

# ============================
# STREAMLIT UI COMPONENTS
# ============================

def render_header():
    """Render application header"""
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .main-header h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
        }
        .main-header p {
            color: rgba(255, 255, 255, 0.9);
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
        }
        </style>
        <div class="main-header">
            <h1>🎯 AI Interview Training System Pro</h1>
            <p>Latihan interview AI-powered dengan feedback real-time dan analytics mendalam</p>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar(db: DatabaseManager):
    """Render enhanced sidebar"""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/667eea/ffffff?text=InterviewAI", use_container_width=True)
        
        st.markdown("---")
        
        # Model selection
        st.subheader("⚙️ Pengaturan")
        model_choice = st.selectbox(
            "Model AI",
            ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            help="Pilih model AI untuk interview"
        )
        
        difficulty = st.select_slider(
            "Tingkat Kesulitan",
            options=["Mudah", "Sedang", "Sulit", "Ahli"],
            value="Sedang"
        )
        
        enable_voice = st.checkbox("🎤 Aktifkan Voice (TTS)", value=False, 
                                   help="Text-to-speech untuk membacakan pertanyaan")
        enable_camera = st.checkbox("📹 Aktifkan Camera", value=False,
                                    help="Mode video interview dengan kamera")
        enable_timer = st.checkbox("⏱️ Aktifkan Timer", value=True)
        
        st.markdown("---")
        
        # Quick stats
        if 'user_id' in st.session_state:
            st.subheader("📊 Quick Stats")
            analytics = db.get_analytics_data(st.session_state.user_id)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Interview", analytics['total_interviews'])
            with col2:
                st.metric("Avg Score", f"{analytics['avg_score']:.1f}")
            
            if analytics['improvement_rate'] != 0:
                st.metric(
                    "Improvement", 
                    f"{analytics['improvement_rate']:+.1f}%",
                    delta=f"{analytics['improvement_rate']:.1f}%"
                )
        
        st.markdown("---")
        
        # Navigation
        st.subheader("🧭 Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.stage = 'input'
            st.rerun()
        
        if st.button("📚 History", use_container_width=True):
            st.session_state.stage = 'history'
            st.rerun()
        
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state.stage = 'analytics'
            st.rerun()
        
        st.markdown("---")
        
        # Feature info
        st.subheader("🎯 Features")
        with st.expander("📋 Available Features"):
            st.markdown("""
            **✅ Active:**
            - 📝 Text CV Input
            - 📄 PDF CV Upload
            - 📹 Video Interview Mode
            - 🔊 Text-to-Speech
            - 💾 Result Export
            
            **🚧 Coming Soon:**
            - 🎤 Voice Recognition
            - 🤖 AI Voice Response
            - 📊 Advanced Analytics
            """)
        
        st.markdown("---")
        
        # Info
        st.subheader("ℹ️ About")
        st.info("""
        **Technology Stack:**
        - 🤖 OpenAI GPT-4
        - 🎙️ gTTS (Text-to-Speech)
        - 📄 PyPDF2 (PDF Reader)
        - 📹 Streamlit Camera
        - 📊 Plotly Charts
        - 💾 SQLite DB
        - 🚀 Streamlit
        
        **Version:** 2.1 Pro
        """)
        
        # Installation guide
        with st.expander("📦 Installation Requirements"):
            st.code("""
# Install required packages
pip install streamlit
pip install openai
pip install plotly
pip install pandas
pip install PyPDF2
pip install gTTS

# Optional for advanced features
pip install SpeechRecognition
pip install pydub
            """, language="bash")
        
        return model_choice, difficulty, enable_voice, enable_camera, enable_timer

# ============================
# MAIN STREAMLIT APP
# ============================
def main():
    st.set_page_config(
        page_title="AI Interview Training Pro",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            font-weight: 600;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .success-banner {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .warning-banner {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize services
    db = DatabaseManager()
    llm = LLMService()
    
    # Session state initialization
    default_session_state = {
        'user_id': f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'stage': 'input',
        'questions': [],
        'answers': [],
        'answer_metadata': [],
        'current_question_idx': 0,
        'interview_start_time': None,
        'question_start_time': None,
        'model_choice': "gpt-4o",
        'difficulty': "Sedang",
        'enable_voice': False,
        'enable_camera': False,
        'enable_timer': True
    }
    
    for key, value in default_session_state.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Render header
    render_header()
    
    # Render sidebar and get settings
    model_choice, difficulty, enable_voice, enable_camera, enable_timer = render_sidebar(db)
    
    # Store settings in session state
    st.session_state.model_choice = model_choice
    st.session_state.difficulty = difficulty
    st.session_state.enable_voice = enable_voice
    st.session_state.enable_camera = enable_camera
    st.session_state.enable_timer = enable_timer
    
    # Route to appropriate stage
    if st.session_state.stage == 'input':
        show_input_stage(db, llm)
    elif st.session_state.stage == 'interview':
        show_interview_stage(db, llm)
    elif st.session_state.stage == 'results':
        show_results_stage(db, llm)
    elif st.session_state.stage == 'history':
        show_history_stage(db)
    elif st.session_state.stage == 'analytics':
        show_analytics_stage(db)

def show_input_stage(db: DatabaseManager, llm: LLMService):
    """Enhanced input stage with PDF upload"""
    st.header("📝 Profile & Job Target")
    
    # CV Input Method Selection (OUTSIDE FORM)
    st.subheader("📄 CV Input Method")
    cv_input_method = st.radio(
        "Choose how to input your CV:",
        ["Type CV Text", "Upload PDF"],
        horizontal=True,
        key="cv_input_method_main"
    )
    
    # Handle PDF Upload OUTSIDE FORM
    cv_text_from_pdf = ""
    if cv_input_method == "Upload PDF":
        uploaded_file = st.file_uploader(
            "📎 Upload your CV (PDF format)",
            type=['pdf'],
            help="Upload CV dalam format PDF. Ukuran maksimal 10MB",
            key="pdf_uploader_main"
        )
        
        if uploaded_file is not None:
            with st.spinner("📖 Reading PDF..."):
                extracted_text = Utils.extract_text_from_pdf(uploaded_file)
                if extracted_text:
                    cv_text_from_pdf = extracted_text
                    st.success(f"✅ PDF loaded successfully! ({len(cv_text_from_pdf)} characters)")
                    with st.expander("📄 Preview Extracted Text", expanded=False):
                        st.text_area("Extracted Content", cv_text_from_pdf, height=200, disabled=True, key="pdf_preview_main")
                else:
                    st.error("❌ Failed to extract text from PDF. Please try another file or use Type CV Text option.")
        else:
            st.info("👆 Please upload your CV in PDF format to continue")
    
    st.markdown("---")
    
    # Main Form
    with st.form("cv_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Your Profile")
            
            # Personal info
            full_name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="john@example.com")
            
            col_exp, col_edu = st.columns(2)
            with col_exp:
                experience_years = st.number_input("Years of Experience", min_value=0, max_value=50, value=0)
            with col_edu:
                education = st.selectbox(
                    "Education Level",
                    ["SMA/SMK", "D3", "S1", "S2", "S3"]
                )
            
            st.markdown("---")
            
            # CV text input (only show if Type CV Text is selected)
            if cv_input_method == "Type CV Text":
                cv_text_manual = st.text_area(
                    "CV Content",
                    height=300,
                    key="cv_text_input_form",
                    placeholder="""Masukkan CV Anda di sini...

Contoh:
- Pengalaman kerja
- Pendidikan  
- Keahlian (skills)
- Project yang pernah dikerjakan
- Sertifikasi (jika ada)
                    """,
                    help="Semakin detail CV Anda, semakin baik pertanyaan yang akan dihasilkan"
                )
            else:
                cv_text_manual = ""
                if cv_text_from_pdf:
                    st.success(f"✅ Using CV from uploaded PDF ({len(cv_text_from_pdf)} characters)")
                else:
                    st.warning("⚠️ Please upload a PDF file above before submitting")
        
        with col2:
            st.subheader("Job Target")
            
            target_job = st.text_input(
                "Position",
                placeholder="e.g., Software Engineer"
            )
            
            job_category = st.selectbox(
                "Category",
                [cat.value for cat in JobCategory]
            )
            
            skills = st.text_area(
                "Key Skills (optional)",
                height=100,
                placeholder="Python, JavaScript, React..."
            )
            
            st.markdown("---")
            
            st.info("💡 **Tips:**\n\n- Tulis CV minimal 200 kata\n- Sertakan pengalaman spesifik\n- Sebutkan teknologi/tools\n- Jelaskan achievement")
        
        submitted = st.form_submit_button("🚀 Start Interview", type="primary", use_container_width=True)
    
    if submitted:
        # Determine which CV text to use
        if cv_input_method == "Upload PDF":
            cv_text = cv_text_from_pdf
        else:
            cv_text = cv_text_manual
        
        # Validate inputs
        if not cv_text:
            st.error("❌ CV tidak boleh kosong! Mohon upload PDF atau ketik CV Anda.")
            return
            
        is_valid, message = Utils.validate_cv(cv_text)
        
        if not is_valid:
            st.error(f"❌ {message}")
            return
        
        if not target_job:
            st.error("❌ Mohon isi posisi yang dituju!")
            return
        
        with st.spinner("🔄 Analyzing your CV and generating tailored questions..."):
            # Save profile
            profile_data = {
                'full_name': full_name,
                'email': email,
                'cv_text': cv_text,
                'target_job': target_job,
                'job_category': job_category,
                'experience_years': experience_years,
                'education_level': education,
                'skills': skills.split(',') if skills else []
            }
            
            db.save_user_profile(st.session_state.user_id, profile_data)
            
            # Generate questions
            analysis_result = llm.analyze_cv_and_generate_questions(
                cv_text, 
                target_job,
                st.session_state.difficulty
            )
            
            # Initialize all required state
            st.session_state.cv_text = cv_text
            st.session_state.target_job = target_job
            st.session_state.profile_data = profile_data
            st.session_state.analysis = analysis_result.get('analysis', {})
            st.session_state.questions = analysis_result.get('questions', [])
            st.session_state.answers = []
            st.session_state.answer_metadata = []
            st.session_state.current_question_idx = 0
            st.session_state.session_id = Utils.generate_session_id()
            st.session_state.interview_start_time = time.time()
            st.session_state.question_start_time = time.time()
            st.session_state.stage = 'interview'
            
            st.success("✅ Analysis complete! Starting interview...")
            time.sleep(1)
            st.rerun()

def show_interview_stage(db: DatabaseManager, llm: LLMService):
    """Enhanced interview stage with camera and voice"""
    st.header("🎤 Interview in Progress")
    
    # Enable camera option
    use_camera = st.session_state.get('enable_camera', False)
    use_voice = st.session_state.get('enable_voice', False)
    
    # Progress tracking
    total_questions = len(st.session_state.questions)
    current_idx = st.session_state.current_question_idx
    progress = (current_idx) / total_questions if total_questions > 0 else 0
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.progress(progress)
    with col2:
        st.metric("Question", f"{current_idx + 1}/{total_questions}")
    with col3:
        elapsed = int(time.time() - st.session_state.interview_start_time) if st.session_state.interview_start_time else 0
        st.metric("Time", Utils.format_duration(elapsed))
    
    if current_idx < total_questions:
        current_q = st.session_state.questions[current_idx]
        
        # Camera section
        if use_camera:
            st.markdown("---")
            col_cam1, col_cam2 = st.columns([2, 1])
            with col_cam1:
                camera_image = st.camera_input("📹 Video Interview Mode", key=f"camera_{current_idx}")
                if camera_image:
                    st.caption("✅ Camera active - Interview is being recorded")
            with col_cam2:
                st.info("""
                **📹 Camera Tips:**
                - Look at the camera
                - Good lighting
                - Professional background
                - Smile and be confident!
                """)
        
        # Question card
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 2rem; border-radius: 10px; margin: 1rem 0;'>
                <p style='color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;'>
                    📌 {current_q['category'].upper()} • Difficulty: {current_q.get('difficulty', 'medium').upper()}
                </p>
                <h2 style='color: white; margin: 0.5rem 0;'>{current_q['question']}</h2>
                <p style='color: rgba(255,255,255,0.7); margin: 0.5rem 0 0 0; font-size: 0.9rem;'>
                    💡 {current_q.get('context', '')}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Text-to-speech for question
        if use_voice and gTTS:
            col_voice1, col_voice2 = st.columns([1, 4])
            with col_voice1:
                if st.button("🔊 Dengar Pertanyaan", key=f"tts_{current_idx}"):
                    with st.spinner("🎙️ Generating audio..."):
                        audio_bytes = Utils.text_to_speech(current_q['question'])
                        if audio_bytes:
                            st.audio(audio_bytes, format='audio/mp3')
        
        # Expected points (collapsible)
        with st.expander("🎯 Poin yang Diharapkan"):
            for point in current_q.get('expected_answer_points', []):
                st.write(f"• {point}")
        
        st.markdown("---")
        
        # Answer input
        if use_voice and gTTS:
            tab1, tab2 = st.tabs(["✏️ Type Answer", "🎤 Voice Answer"])
        else:
            tab1, tab2 = st.tabs(["✏️ Type Answer", "🎤 Voice Answer (Install required)"])
        
        with tab1:
            answer_key = f"answer_{current_idx}"
            answer = st.text_area(
                "Your Answer:",
                height=250,
                key=answer_key,
                placeholder="Jelaskan jawaban Anda dengan detail...\n\n- Gunakan contoh konkret\n- Jelaskan approach Anda\n- Sebutkan hasil/impact",
                help=f"Minimal {CONFIG.min_answer_length} karakter"
            )
            
            # Character count
            char_count = len(answer) if answer else 0
            col_count1, col_count2 = st.columns([3, 1])
            with col_count2:
                color = "green" if char_count >= CONFIG.min_answer_length else "orange"
                st.markdown(f"<p style='text-align: right; color: {color};'>{char_count} / {CONFIG.min_answer_length} characters</p>", unsafe_allow_html=True)
        
        with tab2:
            if gTTS:
                st.info("🎙️ **Voice Recording Feature**")
                st.write("Record your answer using the audio recorder below:")
                
                # Using streamlit's audio_input (if available in your version)
                try:
                    audio_value = st.audio_input("Record your answer", key=f"audio_{current_idx}")
                    if audio_value:
                        st.success("✅ Audio recorded! (Transcription feature coming soon)")
                        st.info("💡 For now, please also type your answer in the Type Answer tab")
                except AttributeError:
                    st.warning("⚠️ Audio input not available in this Streamlit version. Please use Type Answer tab.")
                
                st.markdown("---")
                st.write("**Planned features:**")
                st.write("- 🎙️ Record audio directly")
                st.write("- 📤 Upload audio file")
                st.write("- 🔄 Automatic transcription with Whisper AI")
                st.write("- ✅ Voice answer validation")
            else:
                st.warning("⚠️ Voice feature requires gTTS library")
                st.code("pip install gTTS", language="bash")
        
        st.markdown("---")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=(current_idx == 0), use_container_width=True):
                st.session_state.current_question_idx -= 1
                st.rerun()
        
        with col2:
            if st.button("⏭️ Skip", use_container_width=True):
                if st.session_state.current_question_idx < len(st.session_state.answers):
                    pass
                else:
                    st.session_state.answers.append("[Skipped]")
                    st.session_state.answer_metadata.append({
                        'response_time': 0,
                        'skipped': True
                    })
                
                st.session_state.current_question_idx += 1
                
                if st.session_state.current_question_idx >= total_questions:
                    st.session_state.stage = 'results'
                
                st.rerun()
        
        with col3:
            if st.button("Next ➡️", type="primary", use_container_width=True):
                if not answer or len(answer) < CONFIG.min_answer_length:
                    st.error(f"⚠️ Jawaban terlalu singkat! Minimal {CONFIG.min_answer_length} karakter.")
                else:
                    if st.session_state.get('question_start_time') is None:
                        st.session_state['question_start_time'] = time.time()
                    
                    try:
                        current_time = time.time()
                        question_start = st.session_state.get('question_start_time', current_time)
                        response_time = int(current_time - question_start)
                    except (TypeError, ValueError):
                        response_time = 0
                    
                    if len(st.session_state.answers) <= current_idx:
                        st.session_state.answers.append(answer)
                        st.session_state.answer_metadata.append({
                            'response_time': response_time,
                            'skipped': False
                        })
                    else:
                        st.session_state.answers[current_idx] = answer
                        st.session_state.answer_metadata[current_idx] = {
                            'response_time': response_time,
                            'skipped': False
                        }
                    
                    st.session_state.current_question_idx += 1
                    st.session_state.question_start_time = time.time()
                    
                    if st.session_state.current_question_idx >= total_questions:
                        st.session_state.stage = 'results'
                    
                    st.success("✅ Answer saved!")
                    time.sleep(0.5)
                    st.rerun()

def show_results_stage(db: DatabaseManager, llm: LLMService):
    """Enhanced results stage with comprehensive feedback"""
    st.header("📊 Interview Results & Feedback")
    
    with st.spinner("🔄 Evaluating your interview performance..."):
        interview_duration = int(time.time() - st.session_state.interview_start_time)
        
        evaluation = llm.evaluate_full_interview(
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.cv_text,
            st.session_state.target_job
        )
        
        scores = evaluation['scores']
        
        result_data = {
            'job_title': st.session_state.target_job,
            'difficulty': st.session_state.difficulty,
            'scores': scores,
            'duration': interview_duration,
            'questions_answered': len([a for a in st.session_state.answers if a != "[Skipped]"]),
            'transcript': json.dumps(list(zip(st.session_state.questions, st.session_state.answers))),
            'detailed_feedback': json.dumps(evaluation),
            'recommendations': json.dumps(evaluation.get('recommendation', {}))
        }
        
        db.save_interview_result(
            st.session_state.session_id,
            st.session_state.user_id,
            result_data
        )
        
        for i, (q, a) in enumerate(zip(st.session_state.questions, st.session_state.answers)):
            if a != "[Skipped]":
                qa_data = {
                    'user_id': st.session_state.user_id,
                    'question_id': i,
                    'category': q['category'],
                    'question': q['question'],
                    'answer': a,
                    'response_time': st.session_state.answer_metadata[i]['response_time']
                }
                db.save_qa_pair(st.session_state.session_id, qa_data)
    
    avg_score = sum(scores.values()) / len(scores)
    grade = Utils.calculate_grade(avg_score)
    passed = avg_score >= CONFIG.passing_score
    
    if passed:
        st.markdown(f"""
            <div class='success-banner'>
                <h2>🎉 Congratulations! You Passed!</h2>
                <p style='margin: 0; font-size: 1.2rem;'>Overall Score: {avg_score:.1f}/100 ({grade})</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class='warning-banner'>
                <h2>💪 Keep Improving!</h2>
                <p style='margin: 0; font-size: 1.2rem;'>Overall Score: {avg_score:.1f}/100 ({grade})</p>
                <p style='margin: 0.5rem 0 0 0;'>You need {CONFIG.passing_score} to pass. You're {CONFIG.passing_score - avg_score:.1f} points away!</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Score", f"{avg_score:.1f}/100", delta=f"{avg_score - 75:.1f} vs benchmark")
    with col2:
        st.metric("Grade", grade)
    with col3:
        st.metric("Duration", Utils.format_duration(interview_duration))
    with col4:
        answered = len([a for a in st.session_state.answers if a != "[Skipped]"])
        st.metric("Answered", f"{answered}/{len(st.session_state.questions)}")
    
    st.markdown("---")
    
    st.subheader("📊 Score Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            VisualizationService.create_radar_chart(scores),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            VisualizationService.create_gauge_chart(avg_score),
            use_container_width=True
        )
    
    st.plotly_chart(
        VisualizationService.create_bar_chart(scores),
        use_container_width=True
    )
    
    st.markdown("---")
    
    st.subheader("💬 Detailed Feedback by Category")
    
    category_feedback = evaluation.get('category_feedback', {})
    
    for category, score in scores.items():
        with st.expander(f"{'🟢' if score >= 75 else '🟡' if score >= 60 else '🔴'} {category.replace('_', ' ').title()} - {score:.0f}/100"):
            feedback_text = category_feedback.get(category, "No specific feedback available")
            st.write(feedback_text)
            
            for i, q in enumerate(st.session_state.questions):
                if q['category'] == category:
                    st.markdown(f"**Question:** {q['question']}")
                    st.markdown(f"**Your Answer:** {st.session_state.answers[i][:200]}...")
                    break
    
    st.markdown("---")
    
    st.subheader("🎯 Overall Assessment")
    st.info(evaluation.get('overall_assessment', 'No overall assessment available'))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("**✅ Strengths**")
        for strength in evaluation.get('strengths', []):
            st.write(f"• {strength}")
    
    with col2:
        st.warning("**⚠️ Areas for Improvement**")
        for weakness in evaluation.get('weaknesses', []):
            st.write(f"• {weakness}")
    
    red_flags = evaluation.get('red_flags', [])
    if red_flags:
        st.error("**🚩 Concerns**")
        for flag in red_flags:
            st.write(f"• {flag}")
    
    st.markdown("---")
    
    st.subheader("💼 Hiring Recommendation")
    recommendation = evaluation.get('recommendation', {})
    
    decision = recommendation.get('decision', 'Maybe')
    confidence = recommendation.get('confidence', 'N/A')
    reasoning = recommendation.get('reasoning', 'No reasoning provided')
    next_steps = recommendation.get('next_steps', [])
    
    decision_color = {
        'Hire': 'success',
        'Maybe': 'warning',
        "Don't Hire": 'error'
    }.get(decision, 'info')
    
    getattr(st, decision_color)(f"""
    **Decision:** {decision} (Confidence: {confidence})
    
    **Reasoning:** {reasoning}
    """)
    
    if next_steps:
        st.write("**Suggested Next Steps:**")
        for step in next_steps:
            st.write(f"• {step}")
    
    st.markdown("---")
    
    st.subheader("🚀 Development Plan")
    dev_plan = evaluation.get('development_plan', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Priority Areas:**")
        for area in dev_plan.get('priority_areas', []):
            st.write(f"• {area}")
    
    with col2:
        st.write("**Suggested Actions:**")
        for action in dev_plan.get('suggested_actions', []):
            st.write(f"• {action}")
    
    if 'timeline' in dev_plan:
        st.info(f"⏱️ **Recommended Timeline:** {dev_plan['timeline']}")
    
    st.markdown("---")
    
    st.subheader("💼 Job Recommendations")
    
    with st.spinner("🔍 Finding matching jobs..."):
        conn = db.get_connection()
        job_market = pd.read_sql_query("SELECT * FROM job_market", conn)
        conn.close()
        
        job_market_list = job_market.to_dict('records')
        
        recommendations = llm.get_job_recommendations(
            st.session_state.cv_text,
            scores,
            job_market_list
        )
    
    if recommendations:
        for i, rec in enumerate(recommendations[:5], 1):
            match_pct = rec.get('match_percentage', 0)
            match_color = "🟢" if match_pct >= 80 else "🟡" if match_pct >= 60 else "🔴"
            
            with st.expander(f"{match_color} {i}. {rec['job_title']} - Match: {match_pct}%"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Why it's a good fit:**")
                    for reason in rec.get('match_reasons', []):
                        st.write(f"• {reason}")
                    
                    if rec.get('skill_gaps'):
                        st.write(f"\n**Skills to develop:**")
                        for gap in rec['skill_gaps']:
                            st.write(f"• {gap}")
                
                with col2:
                    st.metric("Salary Range", rec.get('salary_range', 'N/A'))
                    st.metric("Growth Potential", rec.get('growth_potential', 'N/A'))
                    st.metric("Difficulty", rec.get('difficulty_to_get', 'N/A'))
    else:
        st.info("No specific job recommendations available at this time.")
    
    st.markdown("---")
    
    st.subheader("🎬 What's Next?")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 New Interview", type="primary", use_container_width=True):
            for key in ['questions', 'answers', 'answer_metadata', 'current_question_idx', 
                       'interview_start_time', 'question_start_time', 'session_id']:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.stage = 'input'
            st.rerun()
    
    with col2:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.stage = 'analytics'
            st.rerun()
    
    with col3:
        if st.button("📚 History", use_container_width=True):
            st.session_state.stage = 'history'
            st.rerun()
    
    with col4:
        export_data = {
            'session_id': st.session_state.session_id,
            'date': datetime.now().isoformat(),
            'job_title': st.session_state.target_job,
            'scores': scores,
            'evaluation': evaluation,
            'qa_pairs': list(zip([q['question'] for q in st.session_state.questions], st.session_state.answers))
        }
        
        json_str = Utils.export_to_json(export_data)
        if json_str:
            st.download_button(
                "📥 Download Report",
                json_str,
                file_name=f"interview_report_{st.session_state.session_id}.json",
                mime="application/json",
                use_container_width=True
            )

def show_history_stage(db: DatabaseManager):
    """Enhanced history view with filters"""
    st.header("📚 Interview History")
    
    history = db.get_user_history(st.session_state.user_id, limit=50)
    
    if not history:
        st.info("🔭 No interview history yet. Start your first interview!")
        if st.button("🚀 Start Interview"):
            st.session_state.stage = 'input'
            st.rerun()
        return
    
    st.subheader("📊 Summary Statistics")
    
    total = len(history)
    avg_score = sum(h['total_score'] for h in history) / total if total > 0 else 0
    passed = sum(1 for h in history if h['pass_status'])
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Interviews", total)
    col2.metric("Average Score", f"{avg_score:.1f}")
    col3.metric("Passed", passed)
    col4.metric("Pass Rate", f"{pass_rate:.1f}%")
    
    st.markdown("---")
    
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        job_filter = st.selectbox(
            "Filter by Job",
            ["All"] + list(set(h['job_title'] for h in history))
        )
    
    with col2:
        difficulty_filter = st.selectbox(
            "Filter by Difficulty",
            ["All"] + list(set(h['difficulty_level'] for h in history if h['difficulty_level']))
        )
    
    with col3:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Passed", "Failed"]
        )
    
    filtered_history = history
    if job_filter != "All":
        filtered_history = [h for h in filtered_history if h['job_title'] == job_filter]
    if difficulty_filter != "All":
        filtered_history = [h for h in filtered_history if h['difficulty_level'] == difficulty_filter]
    if status_filter != "All":
        if status_filter == "Passed":
            filtered_history = [h for h in filtered_history if h['pass_status']]
        else:
            filtered_history = [h for h in filtered_history if not h['pass_status']]
    
    st.markdown("---")
    
    st.subheader(f"📋 Interview Records ({len(filtered_history)})")
    
    for record in filtered_history:
        status_icon = "✅" if record['pass_status'] else "❌"
        
        with st.expander(
            f"{status_icon} {record['job_title']} - {record['total_score']:.1f}/100 - {record['created_at']}"
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Score Breakdown:**")
                score_cols = st.columns(4)
                score_cols[0].metric("Communication", f"{record['komunikasi']:.0f}")
                score_cols[1].metric("Problem Solving", f"{record['problem_solving']:.0f}")
                score_cols[2].metric("Leadership", f"{record['leadership']:.0f}")
                score_cols[3].metric("Teamwork", f"{record['teamwork']:.0f}")
                
                score_cols2 = st.columns(4)
                score_cols2[0].metric("Technical", f"{record['pengetahuan_teknis']:.0f}")
                score_cols2[1].metric("Adaptability", f"{record['adaptabilitas']:.0f}")
                score_cols2[2].metric("Creativity", f"{record['kreativitas']:.0f}")
                score_cols2[3].metric("Critical Think", f"{record['critical_thinking']:.0f}")
            
            with col2:
                st.metric("Overall Score", f"{record['total_score']:.1f}/100")
                st.metric("Duration", Utils.format_duration(record['interview_duration']))
                st.metric("Questions", record['questions_answered'])
                st.metric("Status", "PASSED ✅" if record['pass_status'] else "FAILED ❌")
            
            if record['detailed_feedback']:
                try:
                    feedback = json.loads(record['detailed_feedback'])
                    
                    with st.expander("📝 View Detailed Feedback"):
                        st.write("**Overall Assessment:**")
                        st.info(feedback.get('overall_assessment', 'N/A'))
                        
                        col_fb1, col_fb2 = st.columns(2)
                        with col_fb1:
                            st.write("**Strengths:**")
                            for s in feedback.get('strengths', []):
                                st.write(f"• {s}")
                        with col_fb2:
                            st.write("**Improvements:**")
                            for w in feedback.get('weaknesses', []):
                                st.write(f"• {w}")
                except:
                    pass

def show_analytics_stage(db: DatabaseManager):
    """Enhanced analytics dashboard"""
    st.header("📈 Analytics Dashboard")
    
    analytics = db.get_analytics_data(st.session_state.user_id)
    
    if analytics['total_interviews'] == 0:
        st.info("📊 No analytics data yet. Complete some interviews to see your progress!")
        if st.button("🚀 Start Interview"):
            st.session_state.stage = 'input'
            st.rerun()
        return
    
    st.subheader("🎯 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Interviews", analytics['total_interviews'])
    col2.metric("Average Score", f"{analytics['avg_score']:.1f}/100")
    col3.metric(
        "Improvement Rate",
        f"{analytics['improvement_rate']:+.1f}%",
        delta=f"{analytics['improvement_rate']:.1f}%"
    )
    col4.metric("Current Grade", Utils.calculate_grade(analytics['avg_score']))
    
    st.markdown("---")
    
    st.subheader("💪 Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("**🌟 Strongest Area**")
        strongest = analytics['strongest_area']
        st.metric(strongest[0], f"{strongest[1]:.1f}/100")
    
    with col2:
        st.warning("**📚 Area to Improve**")
        weakest = analytics['weakest_area']
        st.metric(weakest[0], f"{weakest[1]:.1f}/100")
    
    st.markdown("---")
    
    st.subheader("📅 Progress Over Time")
    st.plotly_chart(
        VisualizationService.create_progress_timeline(st.session_state.user_id, db),
        use_container_width=True
    )
    
    st.markdown("---")
    
    st.subheader("📊 Category Performance")
    
    category_scores = analytics['category_scores']
    st.plotly_chart(
        VisualizationService.create_bar_chart(category_scores, "Average Score by Category"),
        use_container_width=True
    )
    
    st.markdown("---")
    
    st.subheader("💡 Personalized Recommendations")
    
    if analytics['improvement_rate'] < 0:
        st.warning("""
        **📉 Your scores are declining**
        
        Suggestions:
        - Take a break and review feedback from previous interviews
        - Focus on your weakest areas
        - Practice with easier difficulty levels first
        """)
    elif analytics['improvement_rate'] > 10:
        st.success("""
        **🚀 Great progress!**
        
        Keep it up:
        - Try increasing difficulty level
        - Explore different job positions
        - Share your experience with others
        """)
    else:
        st.info("""
        **📊 Steady progress**
        
        Next steps:
        - Review feedback carefully
        - Practice consistently
        - Focus on weakest categories
        """)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Start New Interview", type="primary", use_container_width=True):
            st.session_state.stage = 'input'
            st.rerun()
    
    with col2:
        if st.button("📚 View History", use_container_width=True):
            st.session_state.stage = 'history'
            st.rerun()

# ============================
# RUN APP
# ============================

if __name__ == "__main__":
    main()