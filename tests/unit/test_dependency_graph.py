import pytest

from app.models.enums import AgentType, SubtaskStatus
from app.models.subtask import Subtask
from app.orchestration.dependency_graph import (
    CycleError,
    DuplicateSubtaskError,
    UnknownDependencyError,
    build_waves,
    get_ready_subtasks,
)


def make(sid: str, deps: list[str] | None = None, **kw) -> Subtask:
    return Subtask(
        id=sid,
        task_id="task_test",
        description=sid,
        agent_type=AgentType.CODER,
        dependencies=deps or [],
        **kw,
    )


def wave_ids(waves):
    return [[s.id for s in w] for w in waves]


def test_example_from_the_plan():
    # A, B->C, A->D, C->D
    subtasks = [make("A"), make("B"), make("C", ["B"]), make("D", ["A", "C"])]
    assert wave_ids(build_waves(subtasks)) == [["A", "B"], ["C"], ["D"]]


def test_linear_chain():
    subtasks = [make("A"), make("B", ["A"]), make("C", ["B"])]
    assert wave_ids(build_waves(subtasks)) == [["A"], ["B"], ["C"]]


def test_all_independent_single_wave():
    subtasks = [make("A"), make("B"), make("C")]
    assert wave_ids(build_waves(subtasks)) == [["A", "B", "C"]]


def test_priority_orders_within_wave():
    subtasks = [make("A", priority=1), make("B", priority=5)]
    assert wave_ids(build_waves(subtasks)) == [["B", "A"]]


def test_cycle_detected():
    subtasks = [make("A", ["C"]), make("B", ["A"]), make("C", ["B"])]
    with pytest.raises(CycleError):
        build_waves(subtasks)


def test_self_dependency_is_a_cycle():
    with pytest.raises(CycleError):
        build_waves([make("A", ["A"])])


def test_unknown_dependency():
    with pytest.raises(UnknownDependencyError):
        build_waves([make("A", ["ghost"])])


def test_duplicate_ids():
    with pytest.raises(DuplicateSubtaskError):
        build_waves([make("A"), make("A")])


def test_empty_plan():
    assert build_waves([]) == []


def test_get_ready_follows_statuses():
    a, b = make("A"), make("B", ["A"])
    assert [s.id for s in get_ready_subtasks([a, b])] == ["A"]

    a.status = SubtaskStatus.SUCCEEDED
    assert [s.id for s in get_ready_subtasks([a, b])] == ["B"]


def test_get_ready_blocked_by_failed_dependency():
    a, b = make("A"), make("B", ["A"])
    a.status = SubtaskStatus.FAILED
    assert get_ready_subtasks([a, b]) == []