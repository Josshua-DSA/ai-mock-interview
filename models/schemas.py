from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ========================
# User Profile Schema
# ========================

class UserProfile(BaseModel):
    user_id: str
    email: Optional[str] = None
    full_name: str
    cv_text: str
    cv_hash: Optional[str] = None
    target_job: str
    job_category: str
    experience_years: int = 0
    education_level: str
    skills: List[str] = []
    preferences: Optional[dict] = None
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        orm_mode = True


# ========================
# Interview Result Schema
# ========================

class InterviewResult(BaseModel):
    user_id: str
    session_id: str
    job_title: str
    difficulty_level: str
    komunikasi: float = 0
    problem_solving: float = 0
    leadership: float = 0
    teamwork: float = 0
    pengetahuan_teknis: float = 0
    adaptabilitas: float = 0
    kreativitas: float = 0
    critical_thinking: float = 0
    total_score: float = 0
    pass_status: bool = False
    interview_duration: Optional[int] = 0
    questions_answered: Optional[int] = 0
    interview_transcript: Optional[str] = None
    detailed_feedback: Optional[str] = None
    recommendations: Optional[str] = None
    created_at: datetime = None

    class Config:
        orm_mode = True


# ========================
# Q&A History Schema
# ========================

class QAHistory(BaseModel):
    user_id: str
    session_id: str
    question_id: int
    category: str
    question: str
    answer: str
    answer_length: int
    response_time: int
    score: Optional[float] = None
    feedback: Optional[str] = None
    timestamp: datetime = None

    class Config:
        orm_mode = True


# ========================
# User Progress Schema
# ========================

class UserProgress(BaseModel):
    user_id: str
    metric_name: str
    metric_value: float
    improvement_rate: float
    recorded_at: datetime

    class Config:
        orm_mode = True


# ========================
# Job Market Schema
# ========================

class JobMarket(BaseModel):
    job_title: str
    category: str
    avg_salary_min: int
    avg_salary_max: int
    demand_level: str
    required_skills: str
    description: str
    updated_at: datetime

    class Config:
        orm_mode = True


# ========================
# Response Schema for AI Generated Questions & Answers
# ========================

class InterviewAnalysis(BaseModel):
    overall_fit: str
    strengths: List[str]
    gaps: List[str]
    recommendation: str
    questions: List[dict]

    class Config:
        orm_mode = True


# ========================
# Schema for Evaluating Answers
# ========================

class AnswerEvaluation(BaseModel):
    score: float
    feedback: str
    strengths: List[str]
    improvements: List[str]
    missing_points: List[str]
    better_answer_example: str

    class Config:
        orm_mode = True


# ========================
# Comprehensive Interview Evaluation Schema
# ========================

class FullInterviewEvaluation(BaseModel):
    scores: dict
    category_feedback: dict
    overall_assessment: str
    strengths: List[str]
    weaknesses: List[str]
    red_flags: List[str]
    recommendation: dict
    development_plan: dict

    class Config:
        orm_mode = True
