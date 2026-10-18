from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Questions / Answers ----------

class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    kind: str
    ref_id: str
    source: str
    snippet: str


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_text: str
    question_type: str
    order_index: int
    # jd | resume | question_bank | dsa_list (coding questions) | llm_generated (no source matched)
    source: Optional[str] = None
    evidence: list[EvidenceOut] = []


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_id: int
    answer_text: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    strengths: Optional[list[str]] = None
    weaknesses: Optional[list[str]] = None
    # True when the feedback was checked against reference passages (listed in evidence).
    grounded: bool = False
    evidence: list[EvidenceOut] = []


class QuestionWithAnswerOut(QuestionOut):
    answer: Optional[AnswerOut] = None


# ---------- Interviews ----------

class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_name: str
    job_title: str
    status: str
    overall_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class InterviewDetailOut(InterviewOut):
    job_description: str
    questions: list[QuestionOut] = []


class ReportOut(BaseModel):
    interview: InterviewOut
    positive_points: list[str] = []
    negative_points: list[str] = []
    summary: Optional[str] = None
    questions: list[QuestionWithAnswerOut] = []
    proctoring_incident_count: int = 0
    proctoring_events: list[dict] = []


# ---------- Proctoring ----------

class ProctoringEventCreate(BaseModel):
    event_type: str
    message: Optional[str] = None
