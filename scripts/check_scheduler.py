from app.agents.planner import create_plan
from app.models.task import Task
from app.orchestration.dependency_graph import build_waves

task = Task(
    user_request="Build a Python REST API for managing tasks. "
    "Include CRUD endpoints, tests, and documentation."
)

plan = create_plan(task)
waves = build_waves(plan.subtasks)

for i, wave in enumerate(waves, start=1):
    print(f"Wave {i}")
    for st in wave:
        print(f"  ├── [{st.agent_type.value}] {st.description}")