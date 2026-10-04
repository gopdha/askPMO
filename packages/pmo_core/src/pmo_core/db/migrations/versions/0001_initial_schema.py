"""Initial schema, exactly as specified in the LLD (never edit; add new migrations instead).

Revision ID: 0001
Revises:
"""

from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

DDL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE app.documents (
  id            uuid PRIMARY KEY,
  filename      text NOT NULL,
  rel_path      text NOT NULL,
  blob_path     text NOT NULL,
  doc_type      text,
  doc_date      date,
  week          int,
  content_hash  text NOT NULL,
  status        text NOT NULL CHECK (status IN ('uploaded','indexed','failed')),
  chunk_count   int  NOT NULL DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (rel_path)
);

CREATE TABLE app.ingest_jobs (
  id               uuid PRIMARY KEY,
  status           text NOT NULL CHECK (status IN ('queued','running','succeeded','failed')),
  document_ids     uuid[] NOT NULL,
  documents_done   int NOT NULL DEFAULT 0,
  chunks_written   int NOT NULL DEFAULT 0,
  error            text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  started_at       timestamptz,
  finished_at      timestamptz
);

CREATE TABLE app.conversations (
  id          uuid PRIMARY KEY,
  profile     text NOT NULL,
  user_id     text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.turns (
  id                uuid PRIMARY KEY,
  conversation_id   uuid NOT NULL REFERENCES app.conversations(id) ON DELETE CASCADE,
  seq               int  NOT NULL,
  user_message      text NOT NULL,
  standalone_query  text,
  answer            text NOT NULL,
  abstained         boolean NOT NULL,
  conflict_note     text,
  citations         jsonb NOT NULL DEFAULT '[]',
  profile           text NOT NULL,
  toggles           jsonb NOT NULL,
  latency_ms        int NOT NULL,
  input_tokens      int,
  output_tokens     int,
  trace_id          text,
  error             text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (conversation_id, seq)
);

CREATE TABLE app.turn_stages (
  turn_id  uuid NOT NULL REFERENCES app.turns(id) ON DELETE CASCADE,
  stage    text NOT NULL,
  ms       int  NOT NULL,
  payload  jsonb NOT NULL,
  PRIMARY KEY (turn_id, stage)
);

CREATE TABLE app.feedback (
  turn_id     uuid PRIMARY KEY REFERENCES app.turns(id) ON DELETE CASCADE,
  rating      text NOT NULL CHECK (rating IN ('up','down')),
  comment     text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.eval_runs (
  id                 uuid PRIMARY KEY,
  profile            text NOT NULL,
  split              text NOT NULL CHECK (split IN ('tune','test','all')),
  git_sha            text NOT NULL,
  config_hash        text NOT NULL,
  golden_version     text NOT NULL,
  model_deployments  jsonb NOT NULL,
  status             text NOT NULL CHECK (status IN ('running','succeeded','failed')),
  aggregates         jsonb,
  started_at         timestamptz NOT NULL DEFAULT now(),
  finished_at        timestamptz
);

CREATE TABLE app.eval_results (
  run_id              uuid NOT NULL REFERENCES app.eval_runs(id) ON DELETE CASCADE,
  question_id         text NOT NULL,
  category            text NOT NULL,
  answer              text,
  abstained           boolean,
  retrieved_ranked    jsonb,
  hit_at_5            real, recall_at_5 real, mrr real, ndcg_at_5 real,
  key_facts_pass      boolean,
  abstention_correct  boolean,
  trap_avoided        boolean,
  faithfulness        real, answer_relevance real, answer_correctness real,
  latency_ms          int,
  cost_usd            real,
  error               text,
  PRIMARY KEY (run_id, question_id)
);
"""


def upgrade() -> None:
    """Create the version-1 schema."""
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    """Drop every version-1 table."""
    for table in (
        "eval_results",
        "eval_runs",
        "feedback",
        "turn_stages",
        "turns",
        "conversations",
        "ingest_jobs",
        "documents",
    ):
        op.execute(f"DROP TABLE IF EXISTS app.{table} CASCADE")
