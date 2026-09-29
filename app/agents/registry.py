from app.agents.base import BaseAgent
from app.agents.coder import CoderAgent
from app.agents.researcher import ResearchAgent
from app.agents.reviewer import ReviewerAgent
from app.models.enums import AgentType

_AGENTS: dict[AgentType, BaseAgent] = {
    AgentType.RESEARCH: ResearchAgent(),
    AgentType.CODER: CoderAgent(),
    AgentType.REVIEWER: ReviewerAgent(),
}


def get_agent(agent_type: AgentType) -> BaseAgent:
    try:
        return _AGENTS[agent_type]
    except KeyError:
        raise KeyError(f"No agent registered for '{agent_type.value}' yet") from None