import asyncio

from app.orchestration.runner import run_task


async def main():
    state = await run_task(
        "Create a small Python FastAPI app with CRUD endpoints for managing tasks."
    )

    task = state["task"]
    print(f"Task {task.id} -> {task.status.value}")
    if state.get("error"):
        print("Error:", state["error"])

    print(f"\nWaves completed: {state.get('waves_completed')}\n")
    for st in state.get("subtasks", []):
        result = state["results"].get(st.id)
        mark = "OK " if result and result.success else "-- "
        print(f"[{mark}] [{st.agent_type.value:9}] {st.status.value:10} {st.description}")


asyncio.run(main())