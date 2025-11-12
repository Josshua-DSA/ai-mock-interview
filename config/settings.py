"""
Configuration and Constants
"""
from dataclasses import dataclass
from enum import Enum


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


# Global config instance
CONFIG = InterviewConfig()

# Database configuration
DB_PATH = 'interview_training.db'

# OpenAI configuration
DEFAULT_MODEL = "gpt-4o"
MODEL_TEMPERATURE = 0.7
MODEL_MAX_TOKENS = 2000