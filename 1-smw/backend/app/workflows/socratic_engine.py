"""LangGraph Socratic Workflow Engine for requirements analysis.

State machine: init -> analyzing -> questioning -> answering -> evaluating -> generating -> completed

Each state transition is triggered by API endpoints (human-in-the-loop pattern).
The StateGraph is used as a compiled state machine that manages the conversation
context and routes between nodes.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.models.schemas import (
    Choice,
    Question,
    RequirementItem,
    SessionOutputs,
    SessionStep,
    SocraticSession,
)
from app.services.llm_client import get_llm_client
from app.services.generator_service import (
    generate_adr,
    generate_mermaid,
    generate_vue_skeleton,
)

logger = logging.getLogger(__name__)


# ── State definition ───────────────────────────────────────────────────

class SocraticState(TypedDict):
    """Full session state for the LangGraph workflow."""
    session_id: str
    requirements: list[dict]
    current_step: str
    current_question_index: int
    questions: list[dict]
    history: list[dict]
    outputs_adr: str
    outputs_mermaid: list[str]
    outputs_skeleton: list[dict]
    error: str


def _serialize_reqs(items: list[RequirementItem]) -> list[dict]:
    return [item.model_dump() for item in items]


def _deserialize_reqs(data: list[dict]) -> list[RequirementItem]:
    return [RequirementItem(**item) for item in data]


def _serialize_qs(items: list[Question]) -> list[dict]:
    return [item.model_dump() for item in items]


def _deserialize_qs(data: list[dict]) -> list[Question]:
    return [Question(**item) for item in data]


# ── Fallback questions ─────────────────────────────────────────────────

def _fallback_questions(reqs: list[RequirementItem]) -> list[dict]:
    result = []
    for req in reqs[:3]:
        result.append({
            "question_id": f"q_{req.id.lower()}",
            "text": (
                f"Please clarify requirement {req.id}: '{req.content}' - "
                f"What are the specific acceptance criteria or edge cases?"
            ),
            "options": [
                {"label": "A", "value": "acceptance_criteria",
                 "description": "Define specific acceptance criteria"},
                {"label": "B", "value": "edge_cases",
                 "description": "Identify edge cases and error scenarios"},
                {"label": "C", "value": "constraints",
                 "description": "Clarify technical constraints and assumptions"},
                {"label": "D", "value": "other",
                 "description": "Provide additional context or clarification"},
            ],
            "context": req.id,
            "question_type": "choice",
        })
    return result


# ── Graph node functions ───────────────────────────────────────────────

def analyze_requirements(state: SocraticState) -> dict:
    """Node: Analyze uploaded requirements."""
    reqs = _deserialize_reqs(state.get("requirements", []))
    session_id = state["session_id"]

    if not reqs:
        return {"current_step": SessionStep.init.value, "error": "No requirements to analyze"}

    req_summary = "\n".join(f"- {r.id}: {r.content}" for r in reqs)
    history = list(state.get("history", []))
    history.append({
        "role": "user",
        "content": f"Analyze the following requirements:\n{req_summary}",
    })

    logger.info("Session %s: Analyzing %d requirements", session_id, len(reqs))
    return {"current_step": SessionStep.analyzing.value, "history": history, "error": ""}


async def generate_questions_node(state: SocraticState) -> dict:
    """Node: Generate Socratic questions via LLM."""
    reqs = _deserialize_reqs(state.get("requirements", []))
    history = list(state.get("history", []))
    session_id = state["session_id"]
    client = get_llm_client()

    req_text = "\n".join(f"- {r.id}: {r.content}" for r in reqs)

    prompt = (
        "You are a Socratic analyst reviewing system requirements. "
        "For the following requirements, generate clarifying questions that:\n"
        "1. Identify ambiguities, gaps, or contradictions\n"
        "2. Probe for missing edge cases\n"
        "3. Challenge assumptions\n"
        "4. Ask about technical constraints and trade-offs\n\n"
        f"Requirements:\n{req_text}\n\n"
        "Generate 3-5 questions. For each question provide:\n"
        "- question_id: unique id (q001, q002, ...)\n"
        "- text: the question text\n"
        "- options: 3-4 multiple choice options with label (A,B,C), value, and description\n"
        "- context: which requirement this relates to\n\n"
        "Output a JSON array of objects with keys: "
        "question_id, text, options (array of {label, value, description}), context, question_type."
    )

    llm_response = await client.chat(
        messages=history + [{"role": "user", "content": prompt}],
        system="You are a structured data generator. Output ONLY valid JSON, no explanations.",
        max_tokens=4096,
    )

    raw = llm_response.strip()
    raw = raw.replace("\x60\x60\x60json\n", "").replace("\x60\x60\x60\n", "")
    raw = raw.replace("\x60\x60\x60", "").strip()

    try:
        questions_data = json.loads(raw)
        if isinstance(questions_data, dict) and "questions" in questions_data:
            questions_data = questions_data["questions"]
    except json.JSONDecodeError:
        logger.warning("Session %s: LLM JSON parse failed, using fallback", session_id)
        questions_data = _fallback_questions(reqs)

    questions: list[Question] = []
    for i, qd in enumerate(questions_data):
        choices = [Choice(**opt) for opt in qd.get("options", [])]
        questions.append(Question(
            question_id=qd.get("question_id", f"q{i+1:03d}"),
            text=qd.get("text", ""),
            options=choices,
            context=qd.get("context", ""),
            question_type=qd.get("question_type", "choice"),
        ))

    if not questions:
        questions = _fallback_questions(reqs)
        questions = [Question(**q) for q in questions]

    history.append({
        "role": "assistant",
        "content": f"Generated {len(questions)} clarifying questions.",
    })

    logger.info("Session %s: Generated %d questions", session_id, len(questions))
    return {
        "current_step": SessionStep.questioning.value,
        "questions": _serialize_qs(questions),
        "current_question_index": 0,
        "history": history,
        "error": "",
    }


def evaluate_answers(state: SocraticState) -> dict:
    """Node: Evaluate collected answers and update requirement statuses."""
    reqs = _deserialize_reqs(state.get("requirements", []))
    history = list(state.get("history", []))
    session_id = state["session_id"]

    for req in reqs:
        if req.answers:
            req.status = "answered"

    history.append({
        "role": "system",
        "content": f"All requirements analyzed. Answers recorded.",
    })

    logger.info("Session %s: Evaluation complete", session_id)
    return {
        "current_step": SessionStep.evaluating.value,
        "requirements": _serialize_reqs(reqs),
        "history": history,
        "error": "",
    }


async def generate_outputs(state: SocraticState) -> dict:
    """Node: Generate ADR, Mermaid diagrams, and Vue skeleton files."""
    history = list(state.get("history", []))
    reqs = _deserialize_reqs(state.get("requirements", []))
    session_id = state["session_id"]

    outputs_adr = ""
    outputs_mermaid: list[str] = []
    outputs_skeleton: list[dict] = []

    try:
        outputs_adr = await generate_adr(history, requirements=reqs)
        logger.info("Session %s: ADR generated (%d chars)", session_id, len(outputs_adr))

        scenarios = [
            "System architecture overview showing how the main components interact",
            "Data flow diagram showing how data moves through the system",
        ]
        for scenario in scenarios:
            try:
                diagram = await generate_mermaid(scenario)
                if diagram:
                    outputs_mermaid.append(diagram)
            except Exception as e:
                logger.warning("Session %s: Mermaid error: %s", session_id, e)

        spec_templates = [
            ("MainDashboard.vue",
             "Main dashboard component with statistics bar, status indicators, activity list."),
            ("RequirementList.vue",
             "Requirement list with searchable table, status badges, expandable rows."),
        ]
        for fname, spec in spec_templates:
            try:
                vue_code = await generate_vue_skeleton(spec)
                if vue_code:
                    outputs_skeleton.append({"path": f"src/views/{fname}", "content": vue_code})
            except Exception as e:
                logger.warning("Session %s: Vue skeleton error for %s: %s", session_id, fname, e)

    except Exception as e:
        logger.error("Session %s: Output generation failed: %s", session_id, e)
        return {"current_step": SessionStep.generating.value, "error": f"Output failed: {e}"}

    history.append({
        "role": "system",
        "content": f"Generated ADR ({len(outputs_adr)} chars), {len(outputs_mermaid)} diagrams, {len(outputs_skeleton)} Vue files.",
    })

    logger.info("Session %s: All outputs generated", session_id)
    return {
        "current_step": SessionStep.completed.value,
        "outputs_adr": outputs_adr,
        "outputs_mermaid": outputs_mermaid,
        "outputs_skeleton": outputs_skeleton,
        "history": history,
        "error": "",
    }


# ── Routing functions ──────────────────────────────────────────────────

def route_analysis(state: SocraticState) -> Literal["generate_questions", "__end__"]:
    return "__end__" if state.get("error") else "generate_questions"


def route_questioning(state: SocraticState) -> Literal["evaluate_answers", "__end__"]:
    return "__end__" if state.get("error") else "evaluate_answers"


def route_evaluating(state: SocraticState) -> Literal["generate_outputs", "__end__"]:
    return "__end__" if state.get("error") else "generate_outputs"


def route_generating(state: SocraticState) -> Literal["__end__"]:
    return "__end__"


# ── Graph construction ─────────────────────────────────────────────────

def build_socratic_graph() -> StateGraph:
    """Build and compile the Socratic workflow StateGraph."""
    workflow = StateGraph(SocraticState)

    workflow.add_node("analyze_requirements", analyze_requirements)
    workflow.add_node("generate_questions", generate_questions_node)
    workflow.add_node("evaluate_answers", evaluate_answers)
    workflow.add_node("generate_outputs", generate_outputs)

    workflow.set_entry_point("analyze_requirements")

    workflow.add_conditional_edges("analyze_requirements", route_analysis)
    workflow.add_conditional_edges("generate_questions", route_questioning)
    workflow.add_conditional_edges("evaluate_answers", route_evaluating)
    workflow.add_conditional_edges("generate_outputs", route_generating)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ── Singleton ──────────────────────────────────────────────────────────

_graph = None


def get_graph() -> StateGraph:
    global _graph
    if _graph is None:
        _graph = build_socratic_graph()
    return _graph


def create_initial_state(session_id: str, requirements: list[RequirementItem]) -> dict:
    """Create the initial LangGraph state for a new session."""
    return {
        "session_id": session_id,
        "requirements": _serialize_reqs(requirements),
        "current_step": SessionStep.init.value,
        "current_question_index": 0,
        "questions": [],
        "history": [],
        "outputs_adr": "",
        "outputs_mermaid": [],
        "outputs_skeleton": [],
        "error": "",
    }
