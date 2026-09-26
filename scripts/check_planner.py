from app.agents.planner import create_plan
from app.models.task import Task

task = Task(user_request="Build a Python REST API for managing tasks. Include CRUD endpoints, tests, and documentation.")

plan = create_plan(task)

print(f"Plan {plan.id} — {len(plan.subtasks)} subtasks\n")
for st in plan.subtasks:
    deps = ", ".join(st.dependencies) or "none"
    print(f"[{st.agent_type.value:9}] {st.id}  (deps: {deps})")
    print(f"            {st.description}\n")