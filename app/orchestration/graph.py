import asyncio

from langgraph.graph import END, START, StateGraph

from app.agents.planner import create_plan, PlanValidationError
from app.models.enums import TaskStatus
from app.orchestration.dependency_graph import build_waves, SchedulingError
from app.orchestration.executor import MAX_CONCURRENT_AGENTS, run_wave
from app.orchestration.state import GraphState

MAX_WAVES = 25  # circuit breaker: never loop forever even if something's wrong


def plan_node(state: GraphState) -> GraphState:
    task = state["task"]
    task.status = TaskStatus.PLANNING
    task.touch()
    try:
        plan = create_plan(task)
    except (PlanValidationError, ValueError) as e:
        task.status = TaskStatus.FAILED
        return {**state, "error": f"Planning failed: {e}"}

    task.plan_id = plan.id
    task.status = TaskStatus.PLANNED
    task.touch()
    return {
        **state,
        "plan": plan,
        "subtasks": plan.subtasks,
        "results": {},
        "waves_completed": 0,
        "error": None,
    }


def validate_plan_node(state: GraphState) -> GraphState:
    if state.get("error"):
        return state
    try:
        build_waves(state["subtasks"])
    except SchedulingError as e:
        state["task"].status = TaskStatus.FAILED
        return {**state, "error": f"Invalid plan: {e}"}
    return state


async def execute_node(state: GraphState) -> GraphState:
    if state.get("error"):
        return state

    task = state["task"]
    task.status = TaskStatus.EXECUTING
    task.touch()

    subtasks = state["subtasks"]
    results = state["results"]
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_AGENTS)
    waves_run = 0

    while waves_run < MAX_WAVES:
        ran = await run_wave(subtasks, results, task.id, task.user_request, semaphore)
        if not ran:
            break
        waves_run += 1

    unresolved = [s for s in subtasks if s.status.value in ("pending", "running")]
    if unresolved:
        return {
            **state,
            "waves_completed": waves_run,
            "error": f"Execution stalled: {len(unresolved)} subtask(s) never became ready "
                     f"(likely blocked by a failed dependency)",
        }

    return {**state, "waves_completed": waves_run}


def aggregate_node(state: GraphState) -> GraphState:
    task = state["task"]
    subtasks = state["subtasks"]
    results = state["results"]

    if state.get("error"):
        task.status = TaskStatus.FAILED
        task.touch()
        return state

    failed = [s for s in subtasks if s.status.value == "failed"]
    if failed:
        task.status = TaskStatus.FAILED
        error = f"{len(failed)} subtask(s) failed: " + ", ".join(
            f"{s.id} ({results[s.id].error})" for s in failed
        )
        task.touch()
        return {**state, "error": error}

    task.status = TaskStatus.COMPLETED
    task.touch()
    return state


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("plan", plan_node)
    graph.add_node("validate_plan", validate_plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("aggregate", aggregate_node)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "validate_plan")
    graph.add_edge("validate_plan", "execute")
    graph.add_edge("execute", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()