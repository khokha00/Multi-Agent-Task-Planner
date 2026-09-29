import asyncio

import pytest

from app.agents import base as base_module
from app.agents.coder import CoderAgent
from app.agents.researcher import ResearchAgent
from app.agents.reviewer import ReviewerAgent
from app.config import settings
from app.models.context import AgentContext
from app.models.enums import AgentType
from app.models.result import AgentResult
from app.models.subtask import Subtask


def make_subtask(agent_type: AgentType) -> Subtask:
    return Subtask(task_id="task_t", description="do it", agent_type=agent_type)


def make_context(subtask: Subtask, deps=None) -> AgentContext:
    return AgentContext(
        task_id="task_t",
        subtask_id=subtask.id,
        user_goal="Build a thing",
        dependency_results=deps or {},
    )


def fake_llm(payload):
    def _fake(*args, **kwargs):
        return payload
    return _fake


def run(agent, subtask, ctx) -> AgentResult:
    return asyncio.run(agent.run(subtask, ctx))


def test_research_success(monkeypatch):
    monkeypatch.setattr(
        base_module, "call_structured",
        fake_llm({"summary": "s", "findings": ["f1"], "recommendations": []}),
    )
    st = make_subtask(AgentType.RESEARCH)
    result = run(ResearchAgent(), st, make_context(st))
    assert result.success and result.output["findings"] == ["f1"]
    assert result.duration_seconds is not None


def test_invalid_output_becomes_failed_result_not_exception(monkeypatch):
    monkeypatch.setattr(base_module, "call_structured", fake_llm({"nonsense": 1}))
    st = make_subtask(AgentType.RESEARCH)
    result = run(ResearchAgent(), st, make_context(st))
    assert not result.success
    assert "ValidationError" in result.error


def test_llm_exception_becomes_failed_result(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("ollama down")

    monkeypatch.setattr(base_module, "call_structured", boom)
    st = make_subtask(AgentType.RESEARCH)
    result = run(ResearchAgent(), st, make_context(st))
    assert not result.success and "ollama down" in result.error


def test_coder_writes_files(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "workspace_dir", str(tmp_path))
    monkeypatch.setattr(
        base_module, "call_structured",
        fake_llm({"summary": "s", "files": [{"path": "app/main.py", "content": "print(1)"}]}),
    )
    st = make_subtask(AgentType.CODER)
    result = run(CoderAgent(), st, make_context(st))
    assert result.success
    assert (tmp_path / "task_t" / "app" / "main.py").read_text() == "print(1)"


@pytest.mark.parametrize("bad_path", ["../evil.py", "/etc/evil.py"])
def test_coder_rejects_path_escape(monkeypatch, tmp_path, bad_path):
    monkeypatch.setattr(settings, "workspace_dir", str(tmp_path))
    monkeypatch.setattr(
        base_module, "call_structured",
        fake_llm({"summary": "s", "files": [{"path": bad_path, "content": "x"}]}),
    )
    st = make_subtask(AgentType.CODER)
    result = run(CoderAgent(), st, make_context(st))
    assert not result.success and "escapes workspace" in result.error


def test_reviewer_fail_verdict_is_still_a_successful_run(monkeypatch):
    monkeypatch.setattr(
        base_module, "call_structured",
        fake_llm({"verdict": "fail", "summary": "bad",
                  "issues": [{"severity": "high", "description": "no tests"}]}),
    )
    st = make_subtask(AgentType.REVIEWER)
    result = run(ReviewerAgent(), st, make_context(st))
    assert result.success                      # the agent ran fine
    assert result.output["verdict"] == "FAIL"  # ...and normalized "fail"


def test_reviewer_invalid_verdict_fails(monkeypatch):
    monkeypatch.setattr(
        base_module, "call_structured",
        fake_llm({"verdict": "maybe", "summary": "?", "issues": []}),
    )
    st = make_subtask(AgentType.REVIEWER)
    assert not run(ReviewerAgent(), st, make_context(st)).success


def test_dependency_results_appear_in_prompt():
    dep = AgentResult(subtask_id="dep1", agent_type="research", success=True,
                      output={"summary": "use FastAPI"})
    st = make_subtask(AgentType.CODER)
    prompt = CoderAgent().build_user_prompt(st, make_context(st, {"dep1": dep}))
    assert "use FastAPI" in prompt and "Build a thing" in prompt