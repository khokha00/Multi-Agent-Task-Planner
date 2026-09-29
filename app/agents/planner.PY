from app.llm.client import call_structured
from app.llm.prompts import PLANNER_SYSTEM_PROMPT, build_planner_user_prompt
from app.models.enums import AgentType
from app.models.plan import ExecutionPlan
from app.models.subtask import Subtask
from app.models.task import Task
from app.orchestration.dependency_graph import build_waves

class PlanValidationError(Exception):
    pass


def _validate_dependencies(raw_subtasks: list[dict]) -> None:
    ids = {st["id"] for st in raw_subtasks}
    for st in raw_subtasks:
        for dep in st.get("dependencies", []):
            if dep not in ids:
                raise PlanValidationError(
                    f"Subtask '{st['id']}' depends on unknown id '{dep}'"
                )
    # cycle check via simple DFS
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {st["id"]: WHITE for st in raw_subtasks}
    graph = {st["id"]: st.get("dependencies", []) for st in raw_subtasks}

    def visit(node: str):
        color[node] = GRAY
        for dep in graph[node]:
            if color[dep] == GRAY:
                raise PlanValidationError(f"Circular dependency detected at '{node}'")
            if color[dep] == WHITE:
                visit(dep)
        color[node] = BLACK

    for node in graph:
        if color[node] == WHITE:
            visit(node)


def create_plan(task: Task) -> ExecutionPlan:
    raw = call_structured(
        system_prompt=PLANNER_SYSTEM_PROMPT,
        user_prompt=build_planner_user_prompt(task.user_request),
    )

    if "subtasks" not in raw or not isinstance(raw["subtasks"], list):
        raise PlanValidationError("Response missing 'subtasks' list")

    raw_subtasks = raw["subtasks"]
    if not raw_subtasks:
        raise PlanValidationError("Planner returned zero subtasks")

    _validate_dependencies(raw_subtasks)

    # map raw string ids -> real Subtask objects, preserving the planner's ids
    id_map: dict[str, str] = {}
    subtasks: list[Subtask] = []

    for raw_st in raw_subtasks:
        subtask = Subtask(
            task_id=task.id,
            description=raw_st["description"],
            agent_type=AgentType(raw_st["agent"]),
        )
        id_map[raw_st["id"]] = subtask.id
        subtasks.append(subtask)

    # second pass: translate dependency ids now that every subtask has a real id
    for raw_st, subtask in zip(raw_subtasks, subtasks):
        subtask.dependencies = [id_map[dep] for dep in raw_st.get("dependencies", [])]

    build_waves(subtasks)  # raises if the plan is cyclic or malformed
    return ExecutionPlan(task_id=task.id, subtasks=subtasks)