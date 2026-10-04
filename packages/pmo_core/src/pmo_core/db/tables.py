"""SQLAlchemy Core table definitions mirroring migration 0001 (schema `app`)."""

from __future__ import annotations

from sqlalchemy import (
    REAL,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

metadata = MetaData(schema="app")

documents = Table(
    "documents",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("filename", Text, nullable=False),
    Column("rel_path", Text, nullable=False, unique=True),
    Column("blob_path", Text, nullable=False),
    Column("doc_type", Text),
    Column("doc_date", Date),
    Column("week", Integer),
    Column("content_hash", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("chunk_count", Integer, nullable=False, server_default="0"),
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)

ingest_jobs = Table(
    "ingest_jobs",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("status", Text, nullable=False),
    Column("document_ids", ARRAY(UUID(as_uuid=True)), nullable=False),
    Column("documents_done", Integer, nullable=False, server_default="0"),
    Column("chunks_written", Integer, nullable=False, server_default="0"),
    Column("error", Text),
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
    Column("started_at", DateTime(timezone=True)),
    Column("finished_at", DateTime(timezone=True)),
)

conversations = Table(
    "conversations",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("profile", Text, nullable=False),
    Column("user_id", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)

turns = Table(
    "turns",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("conversation_id", UUID(as_uuid=True), ForeignKey("app.conversations.id"), nullable=False),
    Column("seq", Integer, nullable=False),
    Column("user_message", Text, nullable=False),
    Column("standalone_query", Text),
    Column("answer", Text, nullable=False),
    Column("abstained", Boolean, nullable=False),
    Column("conflict_note", Text),
    Column("citations", JSONB, nullable=False),
    Column("profile", Text, nullable=False),
    Column("toggles", JSONB, nullable=False),
    Column("latency_ms", Integer, nullable=False),
    Column("input_tokens", Integer),
    Column("output_tokens", Integer),
    Column("trace_id", Text),
    Column("error", Text),
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)

turn_stages = Table(
    "turn_stages",
    metadata,
    Column("turn_id", UUID(as_uuid=True), ForeignKey("app.turns.id"), primary_key=True),
    Column("stage", Text, primary_key=True),
    Column("ms", Integer, nullable=False),
    Column("payload", JSONB, nullable=False),
)

feedback = Table(
    "feedback",
    metadata,
    Column("turn_id", UUID(as_uuid=True), ForeignKey("app.turns.id"), primary_key=True),
    Column("rating", Text, nullable=False),
    Column("comment", Text),
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)

eval_runs = Table(
    "eval_runs",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("profile", Text, nullable=False),
    Column("split", Text, nullable=False),
    Column("git_sha", Text, nullable=False),
    Column("config_hash", Text, nullable=False),
    Column("golden_version", Text, nullable=False),
    Column("model_deployments", JSONB, nullable=False),
    Column("status", Text, nullable=False),
    Column("aggregates", JSONB),
    Column("started_at", DateTime(timezone=True), server_default=text("now()")),
    Column("finished_at", DateTime(timezone=True)),
)

eval_results = Table(
    "eval_results",
    metadata,
    Column("run_id", UUID(as_uuid=True), ForeignKey("app.eval_runs.id"), primary_key=True),
    Column("question_id", Text, primary_key=True),
    Column("category", Text, nullable=False),
    Column("answer", Text),
    Column("abstained", Boolean),
    Column("retrieved_ranked", JSONB),
    Column("hit_at_5", REAL),
    Column("recall_at_5", REAL),
    Column("mrr", REAL),
    Column("ndcg_at_5", REAL),
    Column("key_facts_pass", Boolean),
    Column("abstention_correct", Boolean),
    Column("trap_avoided", Boolean),
    Column("faithfulness", REAL),
    Column("answer_relevance", REAL),
    Column("answer_correctness", REAL),
    Column("latency_ms", Integer),
    Column("cost_usd", REAL),
    Column("error", Text),
)
