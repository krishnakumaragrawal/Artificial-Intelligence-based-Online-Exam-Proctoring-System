from sqlalchemy.orm import Session

from proctoring_platform.core.config import Settings
from proctoring_platform.core.security import hash_password
from proctoring_platform.models import Exam, Question, QuestionOption, User, UserRole


def bootstrap_admin(db: Session, settings: Settings) -> None:
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return

    email = settings.bootstrap_admin_email.strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        return

    db.add(
        User(
            email=email,
            username=settings.bootstrap_admin_username,
            password_hash=hash_password(settings.bootstrap_admin_password),
            role=UserRole.admin,
        )
    )
    db.commit()


def seed_sample_exam(db: Session) -> None:
    if db.query(Exam).first() is not None:
        return

    exam = Exam(
        title="Python and Database Fundamentals",
        description="Sample exam for local development and API verification.",
        duration_seconds=15 * 60,
        is_published=True,
    )
    db.add(exam)
    db.flush()

    questions = [
        (
            "Which of the following is true for variable names in Python?",
            ["Only underscores are allowed", "Unlimited length", "Must start with a number", "Must be uppercase"],
            1,
        ),
        (
            "Which SQL command removes an entire table definition?",
            ["DELETE", "DROP TABLE", "PURGE", "REMOVE"],
            1,
        ),
        (
            "Which sorting algorithm has O(n log n) average time complexity?",
            ["Selection sort", "Insertion sort", "Quick sort", "Linear search"],
            2,
        ),
    ]

    for index, (prompt, options, correct_index) in enumerate(questions, start=1):
        question = Question(exam_id=exam.id, prompt=prompt, order_index=index, points=1.0)
        db.add(question)
        db.flush()
        for option_index, body in enumerate(options):
            db.add(
                QuestionOption(
                    question_id=question.id,
                    body=body,
                    is_correct=option_index == correct_index,
                )
            )

    db.commit()
