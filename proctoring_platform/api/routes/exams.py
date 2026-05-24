from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from proctoring_platform.api.deps import get_current_user, require_roles
from proctoring_platform.db.session import get_db
from proctoring_platform.models import Exam, Question, QuestionOption, User, UserRole
from proctoring_platform.schemas import ExamCreate, ExamDetail, ExamSummary
from proctoring_platform.services.exam_service import get_published_exam_or_404

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=List[ExamSummary])
def list_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Exam]:
    return db.query(Exam).filter(Exam.is_published.is_(True)).order_by(Exam.created_at.desc()).all()


@router.get("/{exam_id}", response_model=ExamDetail)
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Exam:
    return get_published_exam_or_404(db, exam_id)


@router.post("", response_model=ExamDetail, status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.instructor, UserRole.admin)),
) -> Exam:
    exam = Exam(
        title=payload.title,
        description=payload.description,
        duration_seconds=payload.duration_seconds,
        is_published=True,
    )
    db.add(exam)
    db.flush()

    for question_payload in payload.questions:
        question = Question(
            exam_id=exam.id,
            prompt=question_payload.prompt,
            order_index=question_payload.order_index,
            points=question_payload.points,
        )
        db.add(question)
        db.flush()
        for option_payload in question_payload.options:
            db.add(
                QuestionOption(
                    question_id=question.id,
                    body=option_payload.body,
                    is_correct=option_payload.is_correct,
                )
            )

    db.commit()
    db.refresh(exam)
    return exam
