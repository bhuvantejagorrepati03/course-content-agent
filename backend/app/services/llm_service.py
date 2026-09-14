"""
LLM service.

OpenAI Responses API when OPENAI_API_KEY / LLM_API_KEY is configured.
Deterministic fallback when no key is present (demo / offline mode).
"""
import logging
from typing import Protocol

from app.config import settings

logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an intelligent Course Content Agent for a university academic platform.

You help students, faculty, and question-paper setters understand course content.

You have been given structured course information that includes:
- Course details (name, code, program, year, regulation, credits, total hours)
- All units with their topics, subtopics, and allocated hours
- Course Outcomes (COs) and their Bloom's taxonomy levels
- CO-PO-PSO mapping matrix with correlation values
- Prescribed textbooks and reference books
- Prerequisites

Your behaviour:
1. ALWAYS answer naturally and conversationally — like a knowledgeable academic tutor.
2. Use the course information provided as your primary source of truth.
3. You CAN explain concepts, compare topics, and give study advice using your general \
knowledge — but always ground explanations in the actual course material provided.
4. When the user asks about a specific unit, topic, textbook, or CO, refer directly \
to the course data.
5. When the user asks a follow-up ("explain that", "the second one", "is it hard"), \
use the conversation history to resolve what "that" or "it" refers to.
6. When the user asks which textbook covers a topic, identify the most relevant book \
from the course data and say so clearly.
7. When the user asks for a study plan, generate one based on the actual units and topics.
8. If something is genuinely not present in the course data, say so honestly rather \
than inventing it.
9. Never invent unit numbers, topic names, textbooks, COs, or page numbers.
10. Format responses clearly using markdown — use bullet points, bold headings, \
and numbered lists where appropriate.
11. Cite the source unit or section when making factual claims about the course.
12. Be encouraging and helpful — this is an academic tool.
"""

# ── Protocol ──────────────────────────────────────────────────────────────────

class LLMProvider(Protocol):
    async def complete(
        self,
        system: str,
        conversation: list[dict],   # [{"role": "user"|"assistant", "content": str}, ...]
    ) -> str: ...


# ── OpenAI Responses API provider ─────────────────────────────────────────────

class OpenAIProvider:
    """Calls the OpenAI Responses API."""

    def __init__(self) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=settings.effective_api_key,
            base_url=settings.llm_base_url,
        )
        self._model = settings.effective_model
        logger.info(
            "OpenAI provider initialised — model=%s  base=%s  key_present=%s",
            self._model,
            settings.llm_base_url,
            bool(settings.effective_api_key),
        )

    async def complete(self, system: str, conversation: list[dict]) -> str:
        try:
            # Build input: flatten conversation into a single string that
            # preserves turn structure for the Responses API `input` field.
            formatted_input = self._format_conversation(conversation)

            resp = await self._client.responses.create(
                model=self._model,
                instructions=system,
                input=formatted_input,
            )
            # Responses API: output is a list of response items
            text_parts: list[str] = []
            for item in resp.output:
                # Each item may be a message with content blocks
                if hasattr(item, "content"):
                    for part in item.content:
                        if hasattr(part, "text"):
                            text_parts.append(part.text)
                # Flat text fallback
                elif hasattr(item, "text"):
                    text_parts.append(item.text)
            result = "".join(text_parts).strip()
            if not result:
                logger.warning("OpenAI returned empty response output")
                return "I wasn't able to generate a response. Please try again."
            return result
        except Exception as exc:
            logger.error("OpenAI completion failed: %s", exc, exc_info=True)
            raise

    @staticmethod
    def _format_conversation(conversation: list[dict]) -> str:
        """
        Flatten the multi-turn conversation list into a single string for
        the Responses API `input` parameter.
        """
        if not conversation:
            return ""
        parts = []
        for msg in conversation:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            parts.append(f"{role}: {content}")
        return "\n\n".join(parts)


# ── Fallback provider (no API key) ────────────────────────────────────────────

class FallbackProvider:
    """
    Returns a structured answer from the course context without calling any
    external API.  Used when no API key is configured.
    """

    async def complete(self, system: str, conversation: list[dict]) -> str:  # noqa: ARG002
        # The last message is the user's question with embedded context
        last = conversation[-1]["content"] if conversation else ""

        import re

        # Pull out the context block we injected
        ctx_match = re.search(r"<course_context>(.*?)</course_context>", last, re.DOTALL)
        ctx = ctx_match.group(1).strip() if ctx_match else last

        # Pull out the actual question
        q_match = re.search(r"<question>(.*?)</question>", last, re.DOTALL)
        question = q_match.group(1).strip() if q_match else last

        q_lower = question.lower()

        # Give something useful from context
        if ctx:
            snippet = ctx[:1200].strip()
            return (
                f"Here is what I found in the course materials:\n\n{snippet}\n\n"
                "*(Running in offline mode — connect an OpenAI API key for full AI responses)*"
            )
        return (
            "I'm running in offline mode without an API key. "
            "Please configure OPENAI_API_KEY in the backend .env file to enable full AI responses."
        )


# ── Factory ───────────────────────────────────────────────────────────────────

def get_llm_provider() -> LLMProvider:
    if settings.has_llm_key:
        logger.info(
            "LLM mode: OpenAI — model=%s",
            settings.effective_model,
        )
        return OpenAIProvider()
    logger.info("LLM mode: Fallback (no API key configured)")
    return FallbackProvider()
