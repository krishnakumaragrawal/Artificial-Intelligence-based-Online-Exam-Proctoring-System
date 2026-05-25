from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from proctoring_platform.models import AttemptStatus, EventSeverity, ReviewOutcome, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SignupRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserPublic(ORMModel):
    id: int
    email: str
    username: str
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class OptionPublic(ORMModel):
    id: int
    body: str


class OptionCreate(BaseModel):
    body: str
    is_correct: bool = False


class QuestionPublic(ORMModel):
    id: int
    prompt: str
    order_index: int
    points: float
    options: List[OptionPublic]


class QuestionCreate(BaseModel):
    prompt: str
    order_index: int
    points: float = 1.0
    options: List[OptionCreate]


class ExamSummary(ORMModel):
    id: int
    title: str
    description: Optional[str]
    duration_seconds: int


class ExamCreate(BaseModel):
    title: str
    description: Optional[str] = None
    duration_seconds: int = Field(gt=0)
    questions: List[QuestionCreate]


class ExamDetail(ExamSummary):
    questions: List[QuestionPublic]


class AttemptCreate(BaseModel):
    exam_id: int
    client_fingerprint: Optional[str] = None


class AttemptPublic(ORMModel):
    id: int
    exam_id: int
    status: AttemptStatus
    started_at: datetime
    due_at: datetime
    submitted_at: Optional[datetime]
    score: Optional[float]
    proctoring_session_id: Optional[int] = None


class AnswerUpsert(BaseModel):
    question_id: int
    selected_option_id: int


class AnswerPublic(ORMModel):
    id: int
    question_id: int
    selected_option_id: int
    answered_at: datetime


class SubmitResult(BaseModel):
    attempt_id: int
    status: AttemptStatus
    score: float
    submitted_at: datetime


class ProctoringEventCreate(BaseModel):
    event_type: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    occurred_at: Optional[datetime] = None
    evidence_asset_id: Optional[int] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class ProctoringEventPublic(ORMModel):
    id: int
    event_type: str
    severity: EventSeverity
    confidence: Optional[float]
    occurred_at: datetime
    received_at: datetime
    payload: Dict[str, Any]
    evidence_asset_id: Optional[int]


class EvidenceAssetPublic(ORMModel):
    id: int
    storage_key: str
    content_type: str
    byte_size: int
    sha256: str
    created_at: datetime


class FrameAnalysisResponse(BaseModel):
    frame_id: str
    signals: Dict[str, Any]
    events: List[ProctoringEventPublic]
    evidence_asset: Optional[EvidenceAssetPublic] = None


class AudioAnalysisResponse(BaseModel):
    signals: Dict[str, Any]
    events: List[ProctoringEventPublic]
    evidence_asset: Optional[EvidenceAssetPublic] = None


class ReviewDecisionCreate(BaseModel):
    outcome: ReviewOutcome
    notes: Optional[str] = None


class ReviewDecisionPublic(ORMModel):
    id: int
    attempt_id: int
    reviewer_id: int
    outcome: ReviewOutcome
    notes: Optional[str]
    created_at: datetime


class ReviewAttemptSummary(BaseModel):
    attempt_id: int
    exam_id: int
    exam_title: str
    candidate_email: str
    candidate_username: str
    status: AttemptStatus
    score: Optional[float]
    started_at: datetime
    due_at: datetime
    submitted_at: Optional[datetime]
    event_count: int
    latest_event_type: Optional[str] = None


class AttemptTimeline(BaseModel):
    attempt: AttemptPublic
    events: List[ProctoringEventPublic]
    evidence_assets: List[EvidenceAssetPublic]
    review_decisions: List[ReviewDecisionPublic]
