from app.models.task import Task
from app.orchestration.graph import build_graph
from app.orchestration.state import GraphState

_graph = build_graph()


async def run_task(user_request: str) -> GraphState:
    task = Task(user_request=user_request)
    initial_state: GraphState = {"task": task}
    final_state = await _graph.ainvoke(initial_state)
    return final_state