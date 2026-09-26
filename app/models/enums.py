from enum import Enum


class TaskStatus(str, Enum):
    QUEUED = "queued"
    PLANNING = "planning"
    PLANNED = "planned"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubtaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(str, Enum):
    PLANNER = "planner"
    RESEARCH = "research"
    CODER = "coder"
    REVIEWER = "reviewer"
    DEBUGGER = "debugger"
    EXECUTOR = "executor"