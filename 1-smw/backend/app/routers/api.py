"""API routes for the 1-SMW Socratic Workflow Engine."""

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.schemas import (
    AnswerRequest,
    AnswerResponse,
    CreateSessionResponse,
    CurrentQuestionResponse,
    ErrorResponse,
    SessionOutputsResponse,
    SessionStatusResponse,
    SocraticSession,
    UploadExcelResponse,
)
from app.services.excel_service import parse_requirements_from_excel
from app.workflows.socratic_engine import create_initial_state, get_graph

logger = logging.getLogger(__name__)

router = APIRouter(tags=["1-SMW Socratic Engine"])

_sessions: dict[str, SocraticSession] = {}
_background_tasks: dict[str, asyncio.Task] = {}
_graph_instance = None


def _get_graph():
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = get_graph()
    return _graph_instance


async def _run_analysis_background(session_id: str) -> None:
    """Run LangGraph analysis in background, updating session state."""
    session = _sessions.get(session_id)
    if not session:
        logger.error("Background task: session %s not found", session_id)
        return

    try:
        initial_state = create_initial_state(session_id, session.requirements)
        graph = _get_graph()
        result = await graph.ainvoke(initial_state, {"configurable": {"thread_id": session_id}})

        # Update session from graph result
        session.current_step = result.get("current_step", session.current_step)
        session.history = result.get("history", session.history)

        # Deserialize questions if present
        questions_data = result.get("questions", [])
        if questions_data:
            from app.models.schemas import Question
            session.questions = [Question(**q) if isinstance(q, dict) else q for q in questions_data]

        logger.info("Session %s: analysis done, step=%s", session_id, session.current_step)
    except asyncio.CancelledError:
        logger.warning("Session %s: background analysis cancelled", session_id)
    except Exception as e:
        logger.error("Session %s: background analysis failed: %s", session_id, e)
        session.error = str(e)
        session.current_step = "init"


@router.post("/session/create", response_model=CreateSessionResponse)
async def create_session():
    """Create a new Socratic analysis session."""
    session_id = str(uuid.uuid4())
    session = SocraticSession(id=session_id)
    _sessions[session_id] = session
    logger.info("Session created: %s", session_id)
    return CreateSessionResponse(session_id=session_id)


@router.post("/session/{session_id}/upload-excel", response_model=UploadExcelResponse)
async def upload_excel(session_id: str, file: UploadFile = File(...)):
    """Upload an Excel requirements file. Analysis runs in background."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel (.xlsx) file")

    # Save file
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{session_id}_{file.filename}"
    content = await file.read()
    file_path.write_bytes(content)

    # Parse requirements
    try:
        requirements = parse_requirements_from_excel(str(file_path))
    except Exception as e:
        logger.error("Excel parse error for session %s: %s", session_id, e)
        raise HTTPException(status_code=400, detail=f"Excel parse failed: {str(e)}")

    if not requirements:
        raise HTTPException(status_code=400, detail="No requirements found")

    session.requirements = requirements
    session.current_step = "analyzing"

    # Start background analysis
    task = asyncio.create_task(_run_analysis_background(session_id))
    _background_tasks[session_id] = task

    return UploadExcelResponse(
        session_id=session_id,
        requirements_count=len(requirements),
        requirements=requirements,
        next_step=session.current_step,
    )


@router.get("/session/{session_id}/current-question", response_model=CurrentQuestionResponse)
async def get_current_question(session_id: str):
    """Get the current Socratic question."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return CurrentQuestionResponse(
        session_id=session_id,
        question=session.questions[session.current_question_index] if session.questions else None,
        total_questions=len(session.questions),
        current_index=session.current_question_index,
        step=session.current_step,
    )


@router.post("/session/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, body: AnswerRequest):
    """Submit an answer to the current question."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Record answer in history
    session.history.append({
        "role": "user",
        "content": body.answer,
    })

    # Advance to next question or mark evaluating
    if session.current_question_index < len(session.questions) - 1:
        session.current_question_index += 1
        session.current_step = "questioning"
        remaining = len(session.questions) - session.current_question_index
        msg = f"下一题 ({session.current_question_index + 1}/{len(session.questions)})"
    else:
        session.current_step = "evaluating"
        remaining = 0
        msg = "所有问题已回答，评估中..."
        # Start evaluation in background
        task = asyncio.create_task(_run_evaluation_background(session_id))
        _background_tasks[session_id] = task

    return AnswerResponse(
        session_id=session_id,
        next_step=session.current_step,
        message=msg,
        remaining_questions=remaining,
    )


async def _run_evaluation_background(session_id: str) -> None:
    """Run evaluation and output generation in background."""
    session = _sessions.get(session_id)
    if not session:
        return

    try:
        graph = _get_graph()
        state = create_initial_state(session_id, session.requirements)
        state["history"] = session.history
        state["current_step"] = "evaluating"
        result = await graph.ainvoke(state, {"configurable": {"thread_id": f"{session_id}_gen"}})

        session.outputs.adr = result.get("outputs_adr", "")
        session.outputs.mermaid_diagrams = result.get("outputs_mermaid", [])
        session.outputs.skeleton_files = result.get("outputs_skeleton", [])
        session.current_step = result.get("current_step", "completed")
        session.history = result.get("history", session.history)
        logger.info("Session %s: outputs generated", session_id)
    except Exception as e:
        logger.error("Session %s: evaluation failed: %s", session_id, e)
        session.error = str(e)
        session.current_step = "questioning"


@router.get("/session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """Get the current session status."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionStatusResponse(
        session_id=session_id,
        step=session.current_step,
        requirements_count=len(session.requirements),
        questions_count=len(session.questions),
        questions_answered=session.current_question_index,
        error=session.error,
    )


@router.get("/session/{session_id}/outputs", response_model=SessionOutputsResponse)
async def get_outputs(session_id: str):
    """Get generated outputs (ADR, diagrams, skeleton files)."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionOutputsResponse(
        session_id=session_id,
        step=session.current_step,
        outputs=session.outputs,
    )


@router.get("/session/{session_id}/diagram/{index}")
async def get_diagram(session_id: str, index: int = 0):
    """Get a specific Mermaid diagram by index."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if index < 0 or index >= len(session.outputs.mermaid_diagrams):
        raise HTTPException(status_code=404, detail="Diagram index out of range")

    return JSONResponse({
        "session_id": session_id,
        "index": index,
        "total": len(session.outputs.mermaid_diagrams),
        "mermaid": session.outputs.mermaid_diagrams[index],
    })


@router.get("/session/{session_id}/skeleton/{index}")
async def get_skeleton(session_id: str, index: int = 0):
    """Get a specific skeleton file by index."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if index < 0 or index >= len(session.outputs.skeleton_files):
        raise HTTPException(status_code=404, detail="Skeleton index out of range")

    return JSONResponse({
        "session_id": session_id,
        "index": index,
        "total": len(session.outputs.skeleton_files),
        "file": session.outputs.skeleton_files[index],
    })


@router.get("/sessions", response_model=list[str])
async def list_sessions():
    """List all active session IDs."""
    return list(_sessions.keys())
