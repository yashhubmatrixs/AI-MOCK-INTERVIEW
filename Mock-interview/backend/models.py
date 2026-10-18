from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    interviews = relationship(
        "Interview", back_populates="user", cascade="all, delete-orphan"
    )


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=False)

    resume_filename = Column(String(255), nullable=True)
    resume_text = Column(Text, nullable=True)

    # pending -> in_progress -> completed
    status = Column(String(50), default="pending")

    overall_score = Column(Float, nullable=True)
    positive_points = Column(JSON, nullable=True)  # list[str]
    negative_points = Column(JSON, nullable=True)  # list[str]
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="interviews")
    questions = relationship(
        "Question",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )
    proctoring_events = relationship(
        "ProctoringEvent", back_populates="interview", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)

    question_text = Column(Text, nullable=False)
    # essay | code | verbal
    question_type = Column(String(20), nullable=False)
    order_index = Column(Integer, nullable=False)
    source = Column(String(20), default="llm_generated")  # jd | resume | question_bank | dsa_list | llm_generated

    created_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="questions")
    answer = relationship(
        "Answer", back_populates="question", uselist=False, cascade="all, delete-orphan"
    )
    # Passages (job description / resume / question bank) this question was based on.
    evidence = relationship(
        "Evidence",
        back_populates="question",
        foreign_keys="Evidence.question_id",
        cascade="all",
        order_by="Evidence.id",
    )


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), unique=True, nullable=False)

    answer_text = Column(Text, nullable=True)
    audio_path = Column(String(500), nullable=True)

    score = Column(Float, nullable=True)  # 0-10
    feedback = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)  # list[str]
    weaknesses = Column(JSON, nullable=True)  # list[str]

    submitted_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="answer")
    # Reference passages the answer was checked against (empty = not checked).
    evidence = relationship(
        "Evidence",
        back_populates="answer",
        foreign_keys="Evidence.answer_id",
        cascade="all",
        order_by="Evidence.id",
    )

    @property
    def grounded(self) -> bool:
        return bool(self.evidence)


class ProctoringEvent(Base):
    __tablename__ = "proctoring_events"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)

    # face_not_detected | multiple_faces | tab_switch
    event_type = Column(String(50), nullable=False)
    message = Column(String(255), nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="proctoring_events")


class Evidence(Base):
    """A source passage behind a question or an answer's feedback.

    Belongs to a question (why was this asked?) or to an answer (what was the feedback
    checked against?). A separate table, so existing databases only gain a new table
    on startup - no ALTER on tables that already hold data.
    """

    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=True, index=True)

    kind = Column(String(20), nullable=False)       # knowledge | jd | resume | bank | dsa
    ref_id = Column(String(10), nullable=False)     # label shown in the UI: S1, J2, R1, B3
    source = Column(String(255), nullable=False)    # e.g. "OOP > Abstraction"
    snippet = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="evidence", foreign_keys=[question_id])
    answer = relationship("Answer", back_populates="evidence", foreign_keys=[answer_id])
