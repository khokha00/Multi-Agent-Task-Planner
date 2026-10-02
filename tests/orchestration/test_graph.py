import asyncio

import pytest

from app.agents import registry as registry_module
from app.models.context import AgentContext
from app.models.enums import AgentType
from app.models.result import AgentResult
from app.models.subtask import Subtask
from app.orchestration.executor import run_wave


class StubAgent:
    def __init__(self, should_fail: set[str] | None = None, delay: float = 0):
        self.should_fail = should_fail or set()
        self.delay = delay
        self.calls: list[str] = []

    async def run(self, subtask: Subtask, context: AgentContext) -> AgentResult:
        self.calls.append(subtask.id)
        if self.delay:
            await asyncio.sleep(self.delay)
        ok = subtask.id not in self.should_fail
        return AgentResult(
            subtask_id=subtask.id,
            agent_type=subtask.agent_type.value,
            success=ok,
            output={"echo": subtask.description} if ok else {},
            error=None if ok else "stub failure",
        )


def make(sid: str, deps=None) -> Subtask:
    return Subtask(
        id=sid, task_id="task_t", description=sid,
        agent_type=AgentType.RESEARCH, dependencies=deps or [],
    )


@pytest.mark.asyncio
async def test_run_wave_runs_ready_subtasks_concurrently(monkeypatch):
    stub = StubAgent()
    monkeypatch.setattr(registry_module, "get_agent", lambda _: stub)

    a, b, c = make("A"), make("B"), make("C", ["A", "B"])
    subtasks = [a, b, c]
    results = {}
    sem = asyncio.Semaphore(5)

    ran = await run_wave(subtasks, results, "task_t", "goal", sem)
    assert {s.id for s in ran} == {"A", "B"}       # C isn't ready yet
    assert a.status.value == "succeeded"
    assert c.status.value == "pending"

    ran2 = await run_wave(subtasks, results, "task_t", "goal", sem)
    assert {s.id for s in ran2} == {"C"}
    assert c.status.value == "succeeded"
    assert "echo" in results["C"].output


@pytest.mark.asyncio
async def test_run_wave_marks_failures_and_blocks_dependents(monkeypatch):
    stub = StubAgent(should_fail={"A"})
    monkeypatch.setattr(registry_module, "get_agent", lambda _: stub)

    a, b = make("A"), make("B", ["A"])
    subtasks = [a, b]
    results = {}
    sem = asyncio.Semaphore(5)

    await run_wave(subtasks, results, "task_t", "goal", sem)
    assert a.status.value == "failed"

    ran2 = await run_wave(subtasks, results, "task_t", "goal", sem)
    assert ran2 == []               # B never becomes ready
    assert b.status.value == "pending"