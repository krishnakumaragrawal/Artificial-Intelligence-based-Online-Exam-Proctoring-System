from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from proctoring_platform.api.deps import require_roles
from proctoring_platform.db.session import get_db
from proctoring_platform.models import ExamAttempt, ReviewDecision, User, UserRole
from proctoring_platform.schemas import (
    AttemptPublic,
    AttemptTimeline,
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
