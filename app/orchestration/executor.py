import asyncio

from app.agents import registry
from app.models.context import AgentContext
from app.models.enums import SubtaskStatus
from app.models.result import AgentResult
from app.models.subtask import Subtask
from app.orchestration.dependency_graph import get_ready_subtasks

MAX_CONCURRENT_AGENTS = 5


async def run_wave(
    subtasks: list[Subtask],
    results: dict[str, AgentResult],
    task_id: str,
    user_goal: str,
    semaphore: asyncio.Semaphore,
) -> list[Subtask]:
    """
    Runs every currently-ready subtask concurrently (bounded by semaphore),
    mutates statuses in place, and returns the ready subtasks that were run.
    """
    ready = get_ready_subtasks(subtasks)
    if not ready:
        return []

    for st in ready:
        st.status = SubtaskStatus.RUNNING
        st.touch()

    async def run_one(st: Subtask) -> AgentResult:
        async with semaphore:
            dep_results = {dep: results[dep] for dep in st.dependencies if dep in results}
            context = AgentContext(
                task_id=task_id,
                subtask_id=st.id,
                user_goal=user_goal,
                dependency_results=dep_results,
            )
            agent = registry.get_agent(st.agent_type)
            return await agent.run(st, context)

    wave_results = await asyncio.gather(*(run_one(st) for st in ready))

    for st, result in zip(ready, wave_results):
        st.attempts += 1
        results[st.id] = result
        st.status = SubtaskStatus.SUCCEEDED if result.success else SubtaskStatus.FAILED
        st.touch()

    return ready