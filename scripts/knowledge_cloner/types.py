"""
Knowledge Cloner — Data types and structures.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime


SourceType = Literal["youtube", "podcast", "article", "xspace", "book", "course", "thread", "file", "repo"]
SourceStatus = Literal["queued", "discovered", "transcribed", "extracted", "failed"]
SourcePriority = Literal["HIGH", "MEDIUM", "LOW"]
PipelinePhase = Literal[
    "init", "discovery", "transcription", "extraction",
    "distillation", "synthesis", "operationalization", "quality"
]
ModelChoice = Literal["gemini-flash", "claude-sonnet"]


@dataclass
class Source:
    id: str
    url: str
    source_type: SourceType
    title: str = ""
    date: str = ""
    duration: str = ""
    priority: SourcePriority = "MEDIUM"
    status: SourceStatus = "queued"
    view_count: int = 0
    error: str = ""
    transcript_path: str = ""
    extraction_path: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "source_type": self.source_type,
            "title": self.title,
            "date": self.date,
            "duration": self.duration,
            "priority": self.priority,
            "status": self.status,
            "view_count": self.view_count,
            "error": self.error,
            "transcript_path": self.transcript_path,
            "extraction_path": self.extraction_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Source":
        return cls(
            id=data["id"],
            url=data.get("url", ""),
            source_type=data.get("source_type", "article"),
            title=data.get("title", ""),
            date=data.get("date", ""),
            duration=data.get("duration", ""),
            priority=data.get("priority", "MEDIUM"),
            status=data.get("status", "queued"),
            view_count=data.get("view_count", 0),
            error=data.get("error", ""),
            transcript_path=data.get("transcript_path", ""),
            extraction_path=data.get("extraction_path", ""),
        )


@dataclass
class ExpertConfig:
    name: str
    slug: str
    domain: str
    created: str = ""
    sources: list = field(default_factory=list)
    phases_completed: list = field(default_factory=list)

    def __post_init__(self):
        if not self.created:
            self.created = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "slug": self.slug,
            "domain": self.domain,
            "created": self.created,
            "sources": [s.to_dict() if isinstance(s, Source) else s for s in self.sources],
            "phases_completed": self.phases_completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExpertConfig":
        config = cls(
            name=data["name"],
            slug=data["slug"],
            domain=data.get("domain", ""),
            created=data.get("created", ""),
            phases_completed=data.get("phases_completed", []),
        )
        config.sources = [
            Source.from_dict(s) if isinstance(s, dict) else s
            for s in data.get("sources", [])
        ]
        return config

    def get_source(self, source_id: str) -> Optional[Source]:
        for s in self.sources:
            if s.id == source_id:
                return s
        return None

    def sources_with_status(self, status: SourceStatus) -> list:
        return [s for s in self.sources if s.status == status]


@dataclass
class CostEstimate:
    phase: str
    model: str
    requests: int
    estimated_cost: float
    description: str = ""

    def __str__(self) -> str:
        return f"  {self.phase}: {self.requests} requests via {self.model} (~${self.estimated_cost:.2f})"
