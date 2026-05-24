"""Initial production schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum("student", "instructor", "reviewer", "admin", name="userrole")
    attempt_status = sa.Enum("active", "submitted", "expired", "voided", name="attemptstatus")
    session_status = sa.Enum("active", "closed", name="proctoringsessionstatus")
    event_severity = sa.Enum("info", "low", "medium", "high", "critical", name="eventseverity")
    review_outcome = sa.Enum(
        "clear",
        "needs_follow_up",
        "violation_confirmed",
        "void_attempt",
        name="reviewoutcome",
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "exams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exams.id"), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("points", sa.Float(), nullable=False),
        sa.UniqueConstraint("exam_id", "order_index", name="uq_question_exam_order"),
    )
    op.create_index("ix_questions_exam_id", "questions", ["exam_id"])

    op.create_table(
        "question_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_question_options_question_id", "question_options", ["question_id"])

    op.create_table(
        "exam_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exams.id"), nullable=False),
        sa.Column("status", attempt_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
    )
    op.create_index("ix_exam_attempts_user_id", "exam_attempts", ["user_id"])
    op.create_index("ix_exam_attempts_exam_id", "exam_attempts", ["exam_id"])

    op.create_table(
        "attempt_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("exam_attempts.id"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("selected_option_id", sa.Integer(), sa.ForeignKey("question_options.id"), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_answer"),
    )
    op.create_index("ix_attempt_answers_attempt_id", "attempt_answers", ["attempt_id"])
    op.create_index("ix_attempt_answers_question_id", "attempt_answers", ["question_id"])

    op.create_table(
        "proctoring_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("exam_attempts.id"), nullable=False, unique=True),
        sa.Column("status", session_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_fingerprint", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_proctoring_sessions_attempt_id", "proctoring_sessions", ["attempt_id"])

    op.create_table(
        "evidence_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("proctoring_sessions.id"), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_assets_session_id", "evidence_assets", ["session_id"])

    op.create_table(
        "proctoring_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("proctoring_sessions.id"), nullable=False),
        sa.Column("evidence_asset_id", sa.Integer(), sa.ForeignKey("evidence_assets.id"), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("severity", event_severity, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_proctoring_events_session_id", "proctoring_events", ["session_id"])
    op.create_index("ix_proctoring_events_event_type", "proctoring_events", ["event_type"])

    op.create_table(
        "review_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("exam_attempts.id"), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("outcome", review_outcome, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_decisions_attempt_id", "review_decisions", ["attempt_id"])
    op.create_index("ix_review_decisions_reviewer_id", "review_decisions", ["reviewer_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=120), nullable=False),
        sa.Column("target_id", sa.String(length=120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_review_decisions_reviewer_id", table_name="review_decisions")
    op.drop_index("ix_review_decisions_attempt_id", table_name="review_decisions")
    op.drop_table("review_decisions")
    op.drop_index("ix_proctoring_events_event_type", table_name="proctoring_events")
    op.drop_index("ix_proctoring_events_session_id", table_name="proctoring_events")
    op.drop_table("proctoring_events")
    op.drop_index("ix_evidence_assets_session_id", table_name="evidence_assets")
    op.drop_table("evidence_assets")
    op.drop_index("ix_proctoring_sessions_attempt_id", table_name="proctoring_sessions")
    op.drop_table("proctoring_sessions")
    op.drop_index("ix_attempt_answers_question_id", table_name="attempt_answers")
    op.drop_index("ix_attempt_answers_attempt_id", table_name="attempt_answers")
    op.drop_table("attempt_answers")
    op.drop_index("ix_exam_attempts_exam_id", table_name="exam_attempts")
    op.drop_index("ix_exam_attempts_user_id", table_name="exam_attempts")
    op.drop_table("exam_attempts")
    op.drop_index("ix_question_options_question_id", table_name="question_options")
    op.drop_table("question_options")
    op.drop_index("ix_questions_exam_id", table_name="questions")
    op.drop_table("questions")
    op.drop_table("exams")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS reviewoutcome")
        op.execute("DROP TYPE IF EXISTS eventseverity")
        op.execute("DROP TYPE IF EXISTS proctoringsessionstatus")
        op.execute("DROP TYPE IF EXISTS attemptstatus")
        op.execute("DROP TYPE IF EXISTS userrole")
