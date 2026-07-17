"""Pydantic models for the Socratic Workflow Engine."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────

class SessionStep(str, Enum):
    init = "init"
    analyzing = "analyzing"
    questioning = "questioning"
    answering = "answering"
    evaluating = "evaluating"
    generating = "generating"
    completed = "completed"


# ── Core data models ───────────────────────────────────────────────────

class Choice(BaseModel):
    """A multiple-choice option."""
    label: str = Field(..., description="Short label, e.g. 'A'")
    value: str = Field(..., description="Value sent back on selection")
    description: str = Field(..., description="Human-readable explanation")


class RequirementItem(BaseModel):
    """A single parsed requirement from an Excel sheet."""
    id: str = Field(..., description="Requirement identifier (e.g. 'REQ-001')")
    content: str = Field(..., description="Requirement text")
    status: str = Field(default="pending", description="pending | analyzed | answered")
    answers: list[str] = Field(default_factory=list, description="Socratic answers collected")


class Question(BaseModel):
    """A Socratic question presented to the user."""
    question_id: str = Field(..., description="Unique question id")
    text: str = Field(..., description="Question text")
    options: list[Choice] = Field(default_factory=list, description="Multiple-choice options")
    context: str = Field(default="", description="Context / which requirement this relates to")
    question_type: str = Field(default="choice", description="choice | free_text")


class SessionOutputs(BaseModel):
    """Generated deliverables."""
    adr: str = Field(default="", description="Architecture Decision Record (Markdown)")
    mermaid_diagrams: list[str] = Field(default_factory=list, description="Mermaid diagram definitions")
    skeleton_files: list[dict] = Field(
        default_factory=list,
        description="List of {path: str, content: str} for Vue skeleton files",
    )


class SocraticSession(BaseModel):
    """Full session state, persisted in-memory dict."""
    id: str = Field(..., description="Session UUID")
    requirements: list[RequirementItem] = Field(default_factory=list)
    current_step: SessionStep = Field(default=SessionStep.init)
    current_question_index: int = Field(default=0)
    questions: list[Question] = Field(default_factory=list)
    history: list[dict] = Field(
        default_factory=list,
        description="Conversation history for LLM context [{role, content}]",
    )
    outputs: SessionOutputs = Field(default_factory=SessionOutputs)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: Optional[str] = None


# ── API request / response models ──────────────────────────────────────

class CreateSessionResponse(BaseModel):
    session_id: str
    message: str = "Session created"


class UploadExcelResponse(BaseModel):
    session_id: str
    requirements_count: int
    requirements: list[RequirementItem]
    next_step: SessionStep


class CurrentQuestionResponse(BaseModel):
    session_id: str
    question: Optional[Question]
    total_questions: int
    current_index: int
    step: SessionStep


class AnswerRequest(BaseModel):
    answer: str
    question_id: Optional[str] = None


class AnswerResponse(BaseModel):
    session_id: str
    next_step: SessionStep
    message: str
    remaining_questions: int


class SessionStatusResponse(BaseModel):
    session_id: str
    step: SessionStep
    requirements_count: int
    questions_count: int
    questions_answered: int
    error: Optional[str]


class SessionOutputsResponse(BaseModel):
    session_id: str
    step: SessionStep
    outputs: SessionOutputs


class ErrorResponse(BaseModel):
    detail: str
