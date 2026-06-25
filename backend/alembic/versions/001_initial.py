"""Initial migration - create users, runs, reports, metrics tables

Revision ID: 001
Revises: None
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Runs table
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("file_name", sa.String(512), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("result_path", sa.String(1024), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("total_classes", sa.Integer(), default=0),
        sa.Column("total_methods", sa.Integer(), default=0),
        sa.Column("tests_generated", sa.Integer(), default=0),
        sa.Column("tests_compiled", sa.Integer(), default=0),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
    )

    # Reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False, index=True),
        sa.Column("class_name", sa.String(512), nullable=False),
        sa.Column("method_name", sa.String(512), nullable=False),
        sa.Column("method_source", sa.Text(), nullable=True),
        sa.Column("strategy", sa.String(128), nullable=True),
        sa.Column("generated_test", sa.Text(), nullable=True),
        sa.Column("compiled", sa.Boolean(), default=False),
        sa.Column("compilation_error", sa.Text(), nullable=True),
        sa.Column("assertion_count", sa.Integer(), default=0),
        sa.Column("score", sa.Float(), default=0.0),
        sa.Column("gpt_tokens_used", sa.Integer(), default=0),
        sa.Column("gpt_cost_usd", sa.Float(), default=0.0),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Metrics table
    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False, index=True),
        sa.Column("total_methods", sa.Integer(), default=0),
        sa.Column("tests_generated", sa.Integer(), default=0),
        sa.Column("tests_compiled", sa.Integer(), default=0),
        sa.Column("avg_score", sa.Float(), default=0.0),
        sa.Column("total_gpt_tokens", sa.Integer(), default=0),
        sa.Column("total_gpt_cost_usd", sa.Float(), default=0.0),
        sa.Column("analysis_duration_s", sa.Float(), default=0.0),
        sa.Column("generation_duration_s", sa.Float(), default=0.0),
        sa.Column("validation_duration_s", sa.Float(), default=0.0),
        sa.Column("total_duration_s", sa.Float(), default=0.0),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("metrics")
    op.drop_table("reports")
    op.drop_table("runs")
    op.drop_table("users")
