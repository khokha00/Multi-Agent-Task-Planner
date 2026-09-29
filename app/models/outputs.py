from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ResearchOutput(BaseModel):
    summary: str
    findings: list[str] = Field(min_length=1)
    recommendations: list[str] = Field(default_factory=list)


class FileOutput(BaseModel):
    path: str
    content: str


class CoderOutput(BaseModel):
    summary: str
    files: list[FileOutput] = Field(min_length=1)


class ReviewIssue(BaseModel):
    severity: Literal["low", "medium", "high"]
    description: str


class ReviewOutput(BaseModel):
    verdict: Literal["PASS", "FAIL"]
    summary: str
    issues: list[ReviewIssue] = Field(default_factory=list)

    @field_validator("verdict", mode="before")
    @classmethod
    def _normalize_verdict(cls, v):
        return v.strip().upper() if isinstance(v, str) else v