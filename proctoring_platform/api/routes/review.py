from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from proctoring_platform.api.deps import require_roles
from proctoring_platform.db.session import get_db
from proctoring_platform.models import Exam, ExamAttempt, ProctoringEvent, ProctoringSession, ReviewDecision, User, UserRole
from proctoring_platform.schemas import (
    AttemptPublic,
    AttemptTimeline,
    ReviewAttemptSummary,
    ReviewDecisionCreate,
    ReviewDecisionPublic,
)
from proctoring_platform.services.exam_service import get_attempt_or_404

router = APIRouter(prefix="/review", tags=["review"])


def _attempt_public(attempt: ExamAttempt) -> AttemptPublic:
    session_id = attempt.proctoring_session.id if attempt.proctoring_session is not None else None
    return AttemptPublic(
        id=attempt.id,
        exam_id=attempt.exam_id,
        status=attempt.status,
        started_at=attempt.started_at,
        due_at=attempt.due_at,
        submitted_at=attempt.submitted_at,
        score=attempt.score,
        proctoring_session_id=session_id,
    )


@router.get("/attempts", response_model=List[ReviewAttemptSummary])
def list_attempts_for_review(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.instructor, UserRole.reviewer, UserRole.admin)),
) -> List[ReviewAttemptSummary]:
    event_count = (
        select(func.count(ProctoringEvent.id))
        .join(ProctoringSession, ProctoringEvent.session_id == ProctoringSession.id)
        .where(ProctoringSession.attempt_id == ExamAttempt.id)
        .correlate(ExamAttempt)
        .scalar_subquery()
    )
    latest_event_type = (
        select(ProctoringEvent.event_type)
        .join(ProctoringSession, ProctoringEvent.session_id == ProctoringSession.id)
        .where(ProctoringSession.attempt_id == ExamAttempt.id)
        .order_by(ProctoringEvent.received_at.desc(), ProctoringEvent.id.desc())
        .limit(1)
        .correlate(ExamAttempt)
        .scalar_subquery()
    )

    rows = (
        db.query(
            ExamAttempt.id.label("attempt_id"),
            ExamAttempt.exam_id,
            Exam.title.label("exam_title"),
            User.email.label("candidate_email"),
            User.username.label("candidate_username"),
            ExamAttempt.status,
            ExamAttempt.score,
            ExamAttempt.started_at,
            ExamAttempt.due_at,
            ExamAttempt.submitted_at,
            event_count.label("event_count"),
            latest_event_type.label("latest_event_type"),
        )
        .join(Exam, ExamAttempt.exam_id == Exam.id)
        .join(User, ExamAttempt.user_id == User.id)
        .order_by(ExamAttempt.started_at.desc())
        .limit(limit)
        .all()
    )

    return [ReviewAttemptSummary(**row._asdict()) for row in rows]


@router.get("/attempts/{attempt_id}/timeline", response_model=AttemptTimeline)
def get_timeline(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.instructor, UserRole.reviewer, UserRole.admin)),
) -> AttemptTimeline:
    attempt = get_attempt_or_404(db, attempt_id)
    session = attempt.proctoring_session
    return AttemptTimeline(
        attempt=_attempt_public(attempt),
        events=session.events if session is not None else [],
        evidence_assets=session.evidence_assets if session is not None else [],
        review_decisions=attempt.review_decisions,
    )


@router.post("/attempts/{attempt_id}/decision", response_model=ReviewDecisionPublic)
def create_decision(
    attempt_id: int,
    payload: ReviewDecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.instructor, UserRole.reviewer, UserRole.admin)),
) -> ReviewDecision:
    attempt = get_attempt_or_404(db, attempt_id)
    decision = ReviewDecision(
        attempt_id=attempt.id,
        reviewer_id=current_user.id,
        outcome=payload.outcome,
        notes=payload.notes,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision
