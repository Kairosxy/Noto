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
