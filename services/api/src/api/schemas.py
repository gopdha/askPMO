"""API contract (Pydantic). The OpenAPI schema generated from these feeds the TypeScript client."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

ProfileName = Literal["baseline", "hybrid", "rerank", "full"]


class Toggles(BaseModel):
    """Per-request flips of the profile's on/off switches."""

    rewrite: bool | None = None
    filter: bool | None = None
    hybrid: bool | None = None
    rerank: bool | None = None
    guardrail: bool | None = None


class HistoryMessage(BaseModel):
    """One prior message, supplied by the eval runner."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Ask a question within a conversation."""

    message: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None
    history: list[HistoryMessage] | None = None  # eval only; ignored when conversation_id is set
    profile: ProfileName = "full"
    overrides: Toggles = Toggles()
    debug: bool = False


class Citation(BaseModel):
    """A validated citation attached to an answer."""

    marker: int
    chunk_id: str
    document_id: UUID
    source: str
    section: str
    quote: str


class CandidateOut(BaseModel):
    """A retrieval candidate with every score it collected."""

    chunk_id: str
    source: str
    section: str
    preview: str  # first 200 characters
    dense_score: float | None
    keyword_score: float | None
    fused_score: float | None
    rerank_score: float | None
    final_score: float | None
    rank: int


class StageOut(BaseModel):
    """One pipeline stage in the response trace."""

    stage: str
    ms: int
    data: dict[str, Any]


class ChatResponse(BaseModel):
    """Answer, citations and the stage trace."""

    conversation_id: UUID
    turn_id: UUID
    trace_id: str
    answer: str
    abstained: bool
    conflict_note: str | None
    citations: list[Citation]
    stages: list[StageOut]
    latency_ms: int


class ProfileOut(BaseModel):
    """A profile and its resolved toggles."""

    name: ProfileName
    toggles: dict[str, bool]


class DocumentOut(BaseModel):
    """A stored document."""

    id: UUID
    filename: str
    rel_path: str
    doc_type: str | None
    doc_date: date | None
    week: int | None
    status: Literal["uploaded", "indexed", "failed"]
    chunk_count: int
    created_at: datetime


class IngestJobOut(BaseModel):
    """Ingest job progress."""

    id: UUID
    status: Literal["queued", "running", "succeeded", "failed"]
    document_ids: list[UUID]
    documents_done: int
    chunks_written: int
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class UploadResponse(BaseModel):
    """Result of an upload: one job for all accepted documents."""

    job_id: UUID
    document_ids: list[UUID]


class ChunkOut(BaseModel):
    """Full chunk text and metadata, for a clicked citation."""

    chunk_id: str
    document_id: str
    text: str
    source: str
    section: str
    doc_type: str
    doc_date: date | None
    week: int | None
    ids: list[str]


class EvalRunOut(BaseModel):
    """An evaluation run with headline aggregates."""

    id: UUID
    profile: str
    split: Literal["tune", "test", "all"]
    git_sha: str
    config_hash: str
    golden_version: str
    status: Literal["running", "succeeded", "failed"]
    aggregates: dict[str, Any] | None
    started_at: datetime
    finished_at: datetime | None


class EvalRunDetail(EvalRunOut):
    """An evaluation run with aggregates per category."""

    model_deployments: dict[str, Any]


class EvalResultOut(BaseModel):
    """One row of eval_results."""

    question_id: str
    category: str
    answer: str | None
    abstained: bool | None
    retrieved_ranked: list[str] | None
    hit_at_5: float | None
    recall_at_5: float | None
    mrr: float | None
    ndcg_at_5: float | None
    key_facts_pass: bool | None
    abstention_correct: bool | None
    trap_avoided: bool | None
    faithfulness: float | None
    answer_relevance: float | None
    answer_correctness: float | None
    latency_ms: int | None
    cost_usd: float | None
    error: str | None


class FeedbackIn(BaseModel):
    """Thumbs up or down on a turn."""

    rating: Literal["up", "down"]
    comment: str | None = Field(default=None, max_length=1000)


class HealthOut(BaseModel):
    """Liveness."""

    status: Literal["ok"]


class ReadyCheck(BaseModel):
    """Result of one dependency check."""

    ok: bool
    error: str | None


class ReadyOut(BaseModel):
    """Readiness: index, database, queue and Foundry."""

    ready: bool
    checks: dict[str, ReadyCheck]


class Problem(BaseModel):
    """RFC 7807 problem details."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
