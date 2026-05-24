import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from proctoring_platform.core.time import now_utc
from proctoring_platform.db.base import Base


class UserRole(str, enum.Enum):
    student = "student"
    instructor = "instructor"
    reviewer = "reviewer"
    admin = "admin"


class AttemptStatus(str, enum.Enum):
    active = "active"
    submitted = "submitted"
    expired = "expired"
    voided = "voided"


class ProctoringSessionStatus(str, enum.Enum):
    active = "active"
    closed = "closed"


class EventSeverity(str, enum.Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ReviewOutcome(str, enum.Enum):
    clear = "clear"
    needs_follow_up = "needs_follow_up"
    violation_confirmed = "violation_confirmed"
    void_attempt = "void_attempt"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(80), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.student)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)

    attempts = relationship("ExamAttempt", back_populates="user")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=False)
    is_published = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)

    questions = relationship(
        "Question",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )
    attempts = relationship("ExamAttempt", back_populates="exam")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    points = Column(Float, nullable=False, default=1.0)

    exam = relationship("Exam", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", order_by="QuestionOption.id")

    __table_args__ = (UniqueConstraint("exam_id", "order_index", name="uq_question_exam_order"),)


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)

    question = relationship("Question", back_populates="options")


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    status = Column(Enum(AttemptStatus), nullable=False, default=AttemptStatus.active)
    started_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    due_at = Column(DateTime(timezone=True), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Float, nullable=True)

    user = relationship("User", back_populates="attempts")
    exam = relationship("Exam", back_populates="attempts")
    answers = relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")
    proctoring_session = relationship("ProctoringSession", back_populates="attempt", uselist=False)
    review_decisions = relationship("ReviewDecision", back_populates="attempt")


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    selected_option_id = Column(Integer, ForeignKey("question_options.id"), nullable=False)
    answered_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)

    attempt = relationship("ExamAttempt", back_populates="answers")
    question = relationship("Question")
    selected_option = relationship("QuestionOption")

    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_answer"),)


class ProctoringSession(Base):
    __tablename__ = "proctoring_sessions"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"), unique=True, nullable=False, index=True)
    status = Column(Enum(ProctoringSessionStatus), nullable=False, default=ProctoringSessionStatus.active)
    started_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    client_fingerprint = Column(String(255), nullable=True)

    attempt = relationship("ExamAttempt", back_populates="proctoring_session")
    events = relationship("ProctoringEvent", back_populates="session", cascade="all, delete-orphan")
    evidence_assets = relationship("EvidenceAsset", back_populates="session", cascade="all, delete-orphan")


class EvidenceAsset(Base):
    __tablename__ = "evidence_assets"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("proctoring_sessions.id"), nullable=False, index=True)
    storage_key = Column(String(500), nullable=False)
    content_type = Column(String(120), nullable=False)
    byte_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)

    session = relationship("ProctoringSession", back_populates="evidence_assets")
    events = relationship("ProctoringEvent", back_populates="evidence_asset")


class ProctoringEvent(Base):
    __tablename__ = "proctoring_events"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("proctoring_sessions.id"), nullable=False, index=True)
    evidence_asset_id = Column(Integer, ForeignKey("evidence_assets.id"), nullable=True)
    event_type = Column(String(80), nullable=False, index=True)
    severity = Column(Enum(EventSeverity), nullable=False)
    confidence = Column(Float, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    payload = Column(JSON, nullable=False, default=dict)

    session = relationship("ProctoringSession", back_populates="events")
    evidence_asset = relationship("EvidenceAsset", back_populates="events")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    outcome = Column(Enum(ReviewOutcome), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)

    attempt = relationship("ExamAttempt", back_populates="review_decisions")
    reviewer = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(120), nullable=False)
    target_type = Column(String(120), nullable=False)
    target_id = Column(String(120), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_utc)
