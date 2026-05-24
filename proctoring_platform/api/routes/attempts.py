from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from proctoring_platform.api.deps import get_current_user
from proctoring_platform.db.session import get_db
from proctoring_platform.models import ExamAttempt, User
from proctoring_platform.schemas import (
    AnswerPublic,
    AnswerUpsert,
    AttemptCreate,
    AttemptPublic,
    ExamDetail,
    SubmitResult,
)
from proctoring_platform.services.exam_service import (
    assert_attempt_owner,
    get_attempt_or_404,
    start_attempt,
    submit_attempt,
    upsert_answer,
)

router = APIRouter(prefix="/attempts", tags=["attempts"])


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


@router.post("", response_model=AttemptPublic)
def create_attempt(
    payload: AttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttemptPublic:
    attempt = start_attempt(db, current_user.id, payload.exam_id, payload.client_fingerprint)
    return _attempt_public(attempt)


@router.get("/{attempt_id}", response_model=AttemptPublic)
def get_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttemptPublic:
    attempt = get_attempt_or_404(db, attempt_id)
    assert_attempt_owner(attempt, current_user.id)
    return _attempt_public(attempt)


@router.get("/{attempt_id}/questions", response_model=ExamDetail)
def get_attempt_questions(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExamDetail:
    attempt = get_attempt_or_404(db, attempt_id)
    assert_attempt_owner(attempt, current_user.id)
    return attempt.exam


@router.post("/{attempt_id}/answers", response_model=AnswerPublic)
def save_answer(
    attempt_id: int,
    payload: AnswerUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnswerPublic:
    attempt = get_attempt_or_404(db, attempt_id)
    assert_attempt_owner(attempt, current_user.id)
    return upsert_answer(db, attempt, payload.question_id, payload.selected_option_id)


@router.post("/{attempt_id}/submit", response_model=SubmitResult)
def submit(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmitResult:
    attempt = get_attempt_or_404(db, attempt_id)
    assert_attempt_owner(attempt, current_user.id)
    submitted = submit_attempt(db, attempt)
    return SubmitResult(
        attempt_id=submitted.id,
        status=submitted.status,
        score=float(submitted.score or 0),
        submitted_at=submitted.submitted_at,
    )
