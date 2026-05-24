from datetime import timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from proctoring_platform.core.time import now_utc
from proctoring_platform.models import (
    AttemptAnswer,
    AttemptStatus,
    Exam,
    ExamAttempt,
    ProctoringSession,
    ProctoringSessionStatus,
    Question,
    QuestionOption,
)


def get_published_exam_or_404(db: Session, exam_id: int) -> Exam:
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.is_published.is_(True)).first()
    if exam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return exam


def get_attempt_or_404(db: Session, attempt_id: int) -> ExamAttempt:
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    return attempt


def assert_attempt_owner(attempt: ExamAttempt, user_id: int) -> None:
    if attempt.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attempt access denied")


def ensure_attempt_active(attempt: ExamAttempt) -> None:
    if attempt.status != AttemptStatus.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Attempt is not active")
    due_at = attempt.due_at
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)
    if now_utc() > due_at:
        attempt.status = AttemptStatus.expired
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Attempt has expired")


def start_attempt(
    db: Session,
    user_id: int,
    exam_id: int,
    client_fingerprint: Optional[str] = None,
) -> ExamAttempt:
    exam = get_published_exam_or_404(db, exam_id)
    attempt = ExamAttempt(
        user_id=user_id,
        exam_id=exam.id,
        due_at=now_utc() + timedelta(seconds=exam.duration_seconds),
    )
    db.add(attempt)
    db.flush()

    session = ProctoringSession(attempt_id=attempt.id, client_fingerprint=client_fingerprint)
    db.add(session)
    db.commit()
    db.refresh(attempt)
    return attempt


def upsert_answer(db: Session, attempt: ExamAttempt, question_id: int, selected_option_id: int) -> AttemptAnswer:
    ensure_attempt_active(attempt)

    question = (
        db.query(Question)
        .filter(Question.id == question_id, Question.exam_id == attempt.exam_id)
        .first()
    )
    if question is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question does not belong to attempt exam")

    option = (
        db.query(QuestionOption)
        .filter(QuestionOption.id == selected_option_id, QuestionOption.question_id == question_id)
        .first()
    )
    if option is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Option does not belong to question")

    answer = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt.id, AttemptAnswer.question_id == question_id)
        .first()
    )
    if answer is None:
        answer = AttemptAnswer(
            attempt_id=attempt.id,
            question_id=question_id,
            selected_option_id=selected_option_id,
        )
        db.add(answer)
    else:
        answer.selected_option_id = selected_option_id
        answer.answered_at = now_utc()

    db.commit()
    db.refresh(answer)
    return answer


def submit_attempt(db: Session, attempt: ExamAttempt) -> ExamAttempt:
    ensure_attempt_active(attempt)

    score = 0.0
    answers = db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id == attempt.id).all()
    for answer in answers:
        if answer.selected_option.is_correct:
            score += float(answer.question.points)

    attempt.status = AttemptStatus.submitted
    attempt.score = score
    attempt.submitted_at = now_utc()

    if attempt.proctoring_session is not None:
        attempt.proctoring_session.status = ProctoringSessionStatus.closed
        attempt.proctoring_session.ended_at = now_utc()

    db.commit()
    db.refresh(attempt)
    return attempt
