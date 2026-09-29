from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.config import settings
from app.models.context import AgentContext
from app.models.enums import AgentType
from app.models.outputs import CoderOutput
from app.tools.filesystem import safe_write


class CoderAgent(BaseAgent):
    agent_type = AgentType.CODER
    output_model = CoderOutput
    max_tokens = 4000
    system_prompt = """You are a coding agent in a multi-agent software system.
You implement your subtask as working code, using any prerequisite results provided.

Respond with ONLY a JSON object of this exact shape:
{
  "summary": "what you built, in one or two sentences",
  "files": [
    {"path": "relative/path/file.py", "content": "full file contents"}
  ]
}
Rules:
- Paths must be relative (no leading slash, no '..').
- Each file's content must be complete, not a diff or a snippet.
- Prefer a small number of focused files."""

    def post_process(
        self, validated: BaseModel, context: AgentContext
    ) -> dict[str, Any]:
        assert isinstance(validated, CoderOutput)
        root = Path(settings.workspace_dir) / context.task_id
        written = [
            str(safe_write(root, f.path, f.content).relative_to(root.resolve()))
            for f in validated.files
        ]
        output = validated.model_dump()
        output["written_files"] = written
        return output