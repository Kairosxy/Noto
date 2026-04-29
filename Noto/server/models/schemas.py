"""所有 HTTP 请求/响应 Pydantic 模型"""

from datetime import datetime, date
from typing import Literal, Optional

from pydantic import BaseModel


# ---- AI ----
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class AIChatRequest(BaseModel):
    messages: list[ChatMessage]
    system: str = ""


ProviderName = Literal["openai", "anthropic", "google"]


class TestConnectionRequest(BaseModel):
    provider: ProviderName
    api_key: str
    base_url: str = ""
    model: str = ""


class SettingsUpdateRequest(BaseModel):
    ai_provider: Optional[ProviderName] = None
    ai_api_key: Optional[str] = None
    ai_base_url: Optional[str] = None
    ai_model: Optional[str] = None
    embedding_provider: Optional[ProviderName] = None
    embedding_api_key: Optional[str] = None
    embedding_base_url: Optional[str] = None
    embedding_model: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None


# ---- Notebooks ----
class NotebookCreate(BaseModel):
    title: str
    goal: str = ""


class Notebook(BaseModel):
    id: str
    title: str
    goal: str
    created_at: datetime


# ---- Ingest ----
class DocumentOut(BaseModel):
    id: str
    notebook_id: str
    filename: str
    mime: str
    pages: int | None
    status: Literal["parsing", "ready", "failed"]
    created_at: datetime


# ---- Chat ----
class ChatSendRequest(BaseModel):
    notebook_id: str
    conversation_id: str | None = None  # None 则新建
    message: str


class CloseConversationRequest(BaseModel):
    conversation_id: str


# ---- Review ----
class RateRequest(BaseModel):
    card_id: str
    rating: Literal["again", "hard", "good", "easy"]


class CardOut(BaseModel):
    id: str
    notebook_id: str
    question: str
    answer: str
    due_at: datetime
    ease: int
    reps: int


# ---- Report ----
class ReportGenerateRequest(BaseModel):
    notebook_id: str
    from_date: date
    to_date: date


class ReportOut(BaseModel):
    id: str
    notebook_id: str
    from_date: date
    to_date: date
    content: str
    generated_at: datetime


# -------------------- v2 additions --------------------

from uuid import UUID

# Skeleton
class SkeletonNodeOut(BaseModel):
    id: UUID
    node_type: Literal["claim", "concept", "question", "pitfall"]
    title: str
    body: str | None
    source_positions: list[dict] | None
    card_source: str
    rejected_at: datetime | None
    merged_into: UUID | None


class LearningDirectionOut(BaseModel):
    id: UUID
    position: int
    title: str
    description: str | None
    estimated_minutes: int | None
    node_ids: list[UUID]


class SkeletonOut(BaseModel):
    id: UUID
    notebook_id: UUID
    space_summary: str | None
    status: str
    directions: list[LearningDirectionOut]
    nodes: list[SkeletonNodeOut]
    generated_at: datetime


class RegenerateSkeletonRequest(BaseModel):
    force: bool = False


# Document
class DocumentSummary(BaseModel):
    document_id: UUID
    summary: str | None


# Card state + evaluation
class CardStateUpdate(BaseModel):
    state: Literal["unread", "thinking", "got_it", "stuck"]
    user_explanation: str | None = None


class EvaluateExplanationRequest(BaseModel):
    card_id: UUID
    user_explanation: str


class EvaluateExplanationResponse(BaseModel):
    verdict: Literal["pass", "can_deepen"]
    feedback: str
    missing_points: list[str]


# Highlights
class HighlightCreate(BaseModel):
    document_id: UUID
    chunk_id: UUID | None = None
    text: str


class HighlightOut(BaseModel):
    id: UUID
    document_id: UUID
    notebook_id: UUID
    chunk_id: UUID | None
    text: str
    created_at: datetime


# Selection-scoped ask
class AskWithContextRequest(BaseModel):
    notebook_id: UUID
    document_id: UUID
    chunk_id: UUID | None
    selected_text: str
    user_question: str
    action: Literal["ask", "mark_stuck", "save_note"] = "ask"


# Reject / merge
class RejectNodeRequest(BaseModel):
    reason: str = ""


class MergeNodeRequest(BaseModel):
    target_node_id: UUID
