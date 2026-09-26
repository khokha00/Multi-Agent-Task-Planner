from app.models.task import Task
from app.models.subtask import Subtask
from app.models.enums import AgentType
from app.models.plan import ExecutionPlan

t = Task(user_request="Build a Python REST API with CRUD endpoints, tests, and docs.")

s1 = Subtask(task_id=t.id, description="Research REST API requirements", agent_type=AgentType.RESEARCH)
s2 = Subtask(task_id=t.id, description="Implement the REST API", agent_type=AgentType.CODER, dependencies=[s1.id])

plan = ExecutionPlan(task_id=t.id, subtasks=[s1, s2])

print(t.model_dump_json(indent=2))
print(plan.model_dump_json(indent=2))