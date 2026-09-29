import asyncio
import json
import time
from typing import Any, ClassVar

from pydantic import BaseModel

from app.config import settings
from app.llm.client import call_structured
from app.models.context import AgentContext
from app.models.enums import AgentType
from app.models.result import AgentResult
from app.models.subtask import Subtask

MAX_DEP_CHARS = 12_000  # per dependency, so one huge result can't blow the context


class BaseAgent:
    agent_type: ClassVar[AgentType]
    system_prompt: ClassVar[str]
    output_model: ClassVar[type[BaseModel]]
    max_tokens: ClassVar[int] = 2000

    def build_user_prompt(self, subtask: Subtask, context: AgentContext) -> str:
        parts = [
            f"Overall goal:\n{context.user_goal}",
            f"Your subtask:\n{subtask.description}",
        ]
        if context.dependency_results:
            parts.append(
                "Results from prerequisite subtasks:\n"
                + self._format_dependencies(context)
            )
        return "\n\n".join(parts)

    def _format_dependencies(self, context: AgentContext) -> str:
        blocks = []
        for dep_id, result in context.dependency_results.items():
            payload = json.dumps(result.output, indent=2)
            if len(payload) > MAX_DEP_CHARS:
                payload = payload[:MAX_DEP_CHARS] + "\n...[truncated]"
            blocks.append(f"[{result.agent_type} / {dep_id}]\n{payload}")
        return "\n\n".join(blocks)

    def post_process(
        self, validated: BaseModel, context: AgentContext
    ) -> dict[str, Any]:
        """Hook for subclasses (e.g. the Coder writes files). Returns the output dict."""
        return validated.model_dump()

    async def run(self, subtask: Subtask, context: AgentContext) -> AgentResult:
        start = time.perf_counter()
        try:
            # call_structured is blocking (requests), so run it in a thread.
            # That's what lets asyncio.gather run agents concurrently in Milestone 5.
            raw = await asyncio.to_thread(
                call_structured,
                self.system_prompt,
                self.build_user_prompt(subtask, context),
                settings.agent_model,
                self.max_tokens,
            )
            validated = self.output_model.model_validate(raw)
            output = self.post_process(validated, context)
            return AgentResult(
                subtask_id=subtask.id,
                agent_type=self.agent_type.value,
                success=True,
                output=output,
                duration_seconds=time.perf_counter() - start,
            )
        except Exception as e:  # deliberate: agents never raise into the orchestrator
            return AgentResult(
                subtask_id=subtask.id,
                agent_type=self.agent_type.value,
                success=False,
                error=f"{type(e).__name__}: {e}",
                duration_seconds=time.perf_counter() - start,
            )