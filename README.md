# Multi-Agent Task Planner

A local, free, open-source multi-agent system that takes a natural-language software request, decomposes it into a dependency graph of subtasks, and executes them with specialized agents, running independent subtasks concurrently.

It runs entirely on your machine with [Ollama](https://ollama.com). There are no paid APIs.

> **Core idea:** the agents are not the architecture. The architecture is **state + orchestration + contracts + execution + failure handling**. The LLM calls are one component.

---

## How it works

```text
User request
     │
     ▼
┌──────────┐   LLM → validated ExecutionPlan (Pydantic)
│  PLAN    │
└────┬─────┘
     ▼
┌──────────┐   Deterministic: unknown deps, duplicates, cycles
│ VALIDATE │
└────┬─────┘
     ▼
┌──────────┐   Loop: get ready subtasks → run wave with asyncio.gather
│ EXECUTE  │   (bounded by a semaphore)
└────┬─────┘
     ▼
┌──────────┐   COMPLETED / FAILED
│ AGGREGATE│
└──────────┘
```

Example of dependency-aware scheduling:

```text
Wave 1:  Research ─┐
         Design  ──┤ run concurrently
Wave 2:  Implement ┘
Wave 3:  Review
```

---

## Tech stack

- Python 3.12+
- Pydantic v2 and pydantic-settings (contracts and config)
- LangGraph (workflow and state orchestration)
- asyncio (concurrent agent execution)
- Ollama (local LLM inference, default `llama3.1:8b`)
- pytest and pytest-asyncio

---

## Project structure

```text
multi-agent-platform/
├── app/
│   ├── config.py                 # Settings (Ollama host, models, workspace dir)
│   ├── models/
│   │   ├── enums.py              # TaskStatus, SubtaskStatus, AgentType
│   │   ├── task.py               # Task
│   │   ├── subtask.py            # Subtask (with dependencies[])
│   │   ├── result.py             # AgentResult
│   │   ├── plan.py               # ExecutionPlan
│   │   ├── context.py            # AgentContext (minimal per-agent contract)
│   │   └── outputs.py            # Per-agent output schemas
│   ├── llm/
│   │   ├── client.py             # Ollama client (JSON-constrained output)
│   │   └── prompts.py            # Planner prompt
│   ├── agents/
│   │   ├── base.py               # BaseAgent (prompt → LLM → validate → result)
│   │   ├── planner.py            # create_plan()
│   │   ├── researcher.py
│   │   ├── coder.py
│   │   ├── reviewer.py
│   │   └── registry.py           # agent_type → agent instance
│   ├── tools/
│   │   └── filesystem.py         # Path-safe file writer
│   └── orchestration/
│       ├── dependency_graph.py   # build_waves(), get_ready_subtasks()
│       ├── executor.py           # run_wave() with concurrency + semaphore
│       ├── state.py              # LangGraph state
│       ├── graph.py              # plan → validate → execute → aggregate
│       └── runner.py             # run_task() entry point
├── tests/
│   ├── unit/                     # scheduler + agent tests (no LLM)
│   └── orchestration/            # executor/graph tests with stub agents
├── scripts/                      # manual check scripts
├── workspace/                    # generated code (gitignored)
├── pytest.ini
└── requirements.txt
```

---

## Quickstart

### 1. Install Ollama and pull a model

```bash
# macOS
brew install ollama
# Linux
curl -fsSL https://ollama.com/install.sh | sh

ollama serve                 # if not already running
ollama pull llama3.1:8b      # or qwen2.5:14b / qwen2.5-coder:7b
```

### 2. Set up the project

```bash
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Optional `.env`:

```env
OLLAMA_HOST=http://localhost:11434
PLANNER_MODEL=llama3.1:8b
AGENT_MODEL=qwen2.5-coder:7b
```

### 3. Run the tests (offline, no LLM needed)

```bash
python -m pytest tests/ -v
```

### 4. Run the full pipeline

```bash
python -m scripts.check_orchestrator
```

Generated code is written to `workspace/<task_id>/`.

---

## License

MIT
