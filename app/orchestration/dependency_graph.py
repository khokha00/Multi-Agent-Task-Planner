from collections import defaultdict

from app.models.enums import SubtaskStatus
from app.models.subtask import Subtask


class SchedulingError(Exception):
    """Base class for scheduling problems."""


class CycleError(SchedulingError):
    pass


class UnknownDependencyError(SchedulingError):
    pass


class DuplicateSubtaskError(SchedulingError):
    pass


def build_waves(subtasks: list[Subtask]) -> list[list[Subtask]]:
    """
    Topologically sort subtasks into waves (Kahn's algorithm, level by level).
    Every subtask in wave N depends only on subtasks in waves < N,
    so everything inside one wave can run concurrently.
    """
    by_id: dict[str, Subtask] = {}
    for st in subtasks:
        if st.id in by_id:
            raise DuplicateSubtaskError(f"Duplicate subtask id '{st.id}'")
        by_id[st.id] = st

    indegree: dict[str, int] = {}
    dependents: dict[str, list[str]] = defaultdict(list)

    for st in subtasks:
        deps = set(st.dependencies)
        for dep in deps:
            if dep not in by_id:
                raise UnknownDependencyError(
                    f"Subtask '{st.id}' depends on unknown id '{dep}'"
                )
            dependents[dep].append(st.id)
        indegree[st.id] = len(deps)

    order = {st.id: i for i, st in enumerate(subtasks)}  # stable ordering

    def sort_key(sid: str):
        # higher priority first, then original plan order
        return (-by_id[sid].priority, order[sid])

    current = sorted((sid for sid, d in indegree.items() if d == 0), key=sort_key)
    waves: list[list[Subtask]] = []
    processed = 0

    while current:
        waves.append([by_id[sid] for sid in current])
        processed += len(current)
        nxt: list[str] = []
        for sid in current:
            for child in dependents[sid]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    nxt.append(child)
        current = sorted(nxt, key=sort_key)

    if processed != len(subtasks):
        stuck = sorted(sid for sid, d in indegree.items() if d > 0)
        raise CycleError(f"Circular dependency among subtasks: {stuck}")

    return waves


def get_ready_subtasks(subtasks: list[Subtask]) -> list[Subtask]:
    """
    Dynamic version used at execution time: PENDING subtasks whose
    dependencies have all SUCCEEDED. This is what the orchestrator will
    call after each wave finishes (Milestone 5).
    """
    status = {st.id: st.status for st in subtasks}
    ready = [
        st
        for st in subtasks
        if st.status == SubtaskStatus.PENDING
        and all(status.get(dep) == SubtaskStatus.SUCCEEDED for dep in st.dependencies)
    ]
    return sorted(ready, key=lambda s: -s.priority)