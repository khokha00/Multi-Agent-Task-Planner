import json
from typing import Any

import requests

from app.config import settings


def call_structured(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    max_tokens: int = 2000,
) -> dict[str, Any]:
    """
    Calls a local Ollama model and expects a JSON object back.
    Raises ValueError if the response isn't valid JSON.
    """
    response = requests.post(
        f"{settings.ollama_host}/api/chat",
        json={
            "model": model or settings.planner_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",  # Ollama enforces valid JSON output when set
            "stream": False,
            "options": {"num_predict": max_tokens},
        },
        timeout=120,
    )
    response.raise_for_status()

    raw = response.json()["message"]["content"].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON:\n{raw}") from e