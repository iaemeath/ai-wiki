"""Generator service: ADR, Mermaid diagrams, and Vue skeleton files via LLM."""

from __future__ import annotations

import logging
from typing import Optional

from app.models.schemas import RequirementItem
from app.services.llm_client import get_llm_client

logger = logging.getLogger(__name__)

SYSTEM_ARCHITECT = (
    "You are a senior software architect. Your job is to produce high-quality "
    "architectural deliverables from structured requirements and Socratic Q&A history."
)


def _build_history_block(history: list[dict]) -> str:
    lines: list[str] = []
    for entry in history:
        role = entry.get("role", "unknown")
        content = entry.get("content", "")
        lines.append(f"[{role.upper()}]\n{content}\n")
    return "\n".join(lines)


def _build_requirements_block(requirements: list[RequirementItem]) -> str:
    lines: list[str] = []
    for req in requirements:
        lines.append(f"- [{req.id}] ({req.status}) {req.content}")
        if req.answers:
            for ans in req.answers:
                lines.append(f"    -> {ans}")
    return "\n".join(lines)


async def generate_adr(
    history: list[dict],
    requirements: Optional[list[RequirementItem]] = None,
) -> str:
    """Generate an Architecture Decision Record in Markdown."""
    client = get_llm_client()
    context = _build_history_block(history)
    if requirements:
        context += "\n\n## Requirements\n" + _build_requirements_block(requirements)

    user_prompt = (
        "Based on the following requirements analysis and Socratic Q&A session,\n"
        "produce a comprehensive Architecture Decision Record (ADR) in Markdown format.\n\n"
        f"{context}\n\n"
        "The ADR must include:\n"
        "1. **Title** - ADR-NNN: Decision Title\n"
        "2. **Status** - Proposed | Accepted | Deprecated\n"
        "3. **Context** - The problem and background\n"
        "4. **Decision** - What was decided and why\n"
        "5. **Consequences** - Trade-offs, risks, benefits\n"
        "6. **Compliance** - How this maps to original requirements\n\n"
        "Use clear, technical language suitable for a project README or documentation."
    )

    return await client.chat(
        messages=[{"role": "user", "content": user_prompt}],
        system=SYSTEM_ARCHITECT,
        max_tokens=4096,
    )


async def generate_mermaid(scenario: str) -> str:
    """Generate a Mermaid diagram definition for a given scenario."""
    client = get_llm_client()

    prompt = (
        f"Generate a Mermaid diagram for the following scenario.\n\n"
        f"Scenario: {scenario}\n\n"
        "Output ONLY valid Mermaid syntax. Do NOT wrap in triple backticks.\n"
        "Choose the most appropriate diagram type: flowchart, sequenceDiagram, "
        "classDiagram, or stateDiagram-v2.\n\n"
        "Keep the diagram clear and informative. Label all nodes and edges meaningfully."
    )

    mermaid_text = await client.chat(
        messages=[{"role": "user", "content": prompt}],
        system="You are a Mermaid diagram expert. Output only valid Mermaid syntax.",
        max_tokens=2048,
    )

    # Strip any code fences the model might still add
    mermaid_text = mermaid_text.strip()
    mermaid_text = mermaid_text.replace("\x60\x60\x60mermaid\n", "")
    mermaid_text = mermaid_text.replace("\x60\x60\x60\n", "")
    if mermaid_text.endswith("\x60\x60\x60"):
        mermaid_text = mermaid_text[:-3]
    return mermaid_text.strip()


async def generate_vue_skeleton(spec: str) -> str:
    """Generate a single-file Vue 3 component skeleton from a specification."""
    client = get_llm_client()

    prompt = (
        f"Generate a Vue 3 Single File Component (Composition API + <script setup>) "
        f"based on the specification below. Use Element Plus component library.\n\n"
        f"Specification:\n{spec}\n\n"
        "Requirements:\n"
        "- Use <template>, <script setup lang=\"ts\">, <style scoped> structure\n"
        "- TypeScript with proper interfaces\n"
        "- Reactive state via ref() / reactive()\n"
        "- Props and emits where appropriate\n"
        "- Loading and empty states\n"
        "- Element Plus components (el-button, el-input, el-table, etc.)\n\n"
        "Output ONLY the .vue file content, no explanations."
    )

    vue_text = await client.chat(
        messages=[{"role": "user", "content": prompt}],
        system="You are a Vue 3 frontend expert. Generate clean, production-ready .vue files.",
        max_tokens=4096,
    )

    # Strip code fences
    vue_text = vue_text.strip()
    vue_text = vue_text.replace("\x60\x60\x60vue\n", "")
    vue_text = vue_text.replace("\x60\x60\x60\n", "")
    if vue_text.endswith("\x60\x60\x60"):
        vue_text = vue_text[:-3]
    return vue_text.strip()
