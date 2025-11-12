import sqlite3
import os

class DatabaseManager:
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

        # Create necessary tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
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
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS interview_results (
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
                            FOREIGN KEY (user_id) REFERENCES user_profiles(user_id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS qa_history (
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
                            FOREIGN KEY (session_id) REFERENCES interview_results(session_id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS user_progress (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id TEXT NOT NULL,
                            metric_name TEXT NOT NULL,
                            metric_value REAL,
                            improvement_rate REAL,
                            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS job_market (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            job_title TEXT NOT NULL,
                            category TEXT,
                            avg_salary_min INTEGER,
                            avg_salary_max INTEGER,
                            demand_level TEXT,
                            required_skills TEXT,
                            description TEXT,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON interview_results(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON qa_history(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON interview_results(created_at)')

        conn.commit()
        conn.close()
        
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
            cursor.executemany('''INSERT INTO job_market (job_title, category, avg_salary_min, avg_salary_max, 
                                                         demand_level, required_skills, description)
                                  VALUES (?, ?, ?, ?, ?, ?, ?)''', jobs)
            conn.commit()

        conn.close()

    def save_user_profile(self, user_id: str, profile_data: dict) -> bool:
        """Save or update user profile"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''INSERT OR REPLACE INTO user_profiles 
                            (user_id, email, full_name, cv_text, target_job, job_category, experience_years, education_level, 
                             skills, preferences, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''', (
                user_id, profile_data.get('email'), profile_data.get('full_name'), profile_data['cv_text'],
                profile_data['target_job'], profile_data.get('job_category'),
                profile_data.get('experience_years', 0), profile_data.get('education_level'),
                ','.join(profile_data.get('skills', [])), json.dumps(profile_data.get('preferences', {}))
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving profile: {str(e)}")
            return False
        
    def get_analytics_data(self, user_id: str):
        """Get analytics data for the given user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Mengambil data analitik berdasarkan riwayat wawancara dan profil
        cursor.execute('''SELECT COUNT(*) FROM interview_results WHERE user_id = ?''', (user_id,))
        total_interviews = cursor.fetchone()[0]

        cursor.execute('''SELECT AVG(total_score) FROM interview_results WHERE user_id = ?''', (user_id,))
        avg_score = cursor.fetchone()[0] or 0

        cursor.execute('''SELECT AVG(total_score) - ? FROM interview_results WHERE user_id = ? ORDER BY created_at LIMIT 1''', (avg_score, user_id))
        improvement_rate = cursor.fetchone()[0] or 0

        # Mendapatkan data kekuatan dan kelemahan berdasarkan kategori
        cursor.execute('''SELECT category, AVG(score) FROM qa_history WHERE user_id = ? GROUP BY category ORDER BY AVG(score) DESC LIMIT 1''', (user_id,))
        strongest_area = cursor.fetchone() or ("None", 0)

        cursor.execute('''SELECT category, AVG(score) FROM qa_history WHERE user_id = ? GROUP BY category ORDER BY AVG(score) ASC LIMIT 1''', (user_id,))
        weakest_area = cursor.fetchone() or ("None", 0)

        # Mengambil skor per kategori dari interview_results
        cursor.execute('''SELECT komunikasi, problem_solving, leadership, teamwork, pengetahuan_teknis, adaptabilitas, kreativitas, critical_thinking
                          FROM interview_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 1''', (user_id,))
        category_scores = cursor.fetchone()

        # Membuat data analitik
        analytics_data = {
            'total_interviews': total_interviews,
            'avg_score': avg_score,
            'improvement_rate': improvement_rate,
            'strongest_area': strongest_area,
            'weakest_area': weakest_area,
            'category_scores': {
                'komunikasi': category_scores[0] if category_scores else 0,
                'problem_solving': category_scores[1] if category_scores else 0,
                'leadership': category_scores[2] if category_scores else 0,
                'teamwork': category_scores[3] if category_scores else 0,
                'pengetahuan_teknis': category_scores[4] if category_scores else 0,
                'adaptabilitas': category_scores[5] if category_scores else 0,
                'kreativitas': category_scores[6] if category_scores else 0,
                'critical_thinking': category_scores[7] if category_scores else 0
            }
        }
        
        conn.close()
        return analytics_data
