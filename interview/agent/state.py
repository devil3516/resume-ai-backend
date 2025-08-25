"""Define the shared values."""

from __future__ import annotations
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class InterviewType(Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    MIXED = "mixed"

class ExperienceLevel(Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    PRINCIPAL = "principal"

@dataclass(kw_only=True)
class State:
    """Main graph state."""

    messages: Annotated[list[AnyMessage], add_messages]
    current_state: str = "start"
    user_metadata: Dict[str, str] = field(default_factory=dict)
    conversation_memory: List[Dict[str, str]] = field(default_factory=list)
    interview_started: bool = False
    
    follow_up_needed: bool = False
    interview_progress: int = 0
    current_question: Optional[str] = None
    user_response: Optional[str] = None
    question_count: int = 0
    job_title: str = field(default = "Software Engineer")
    company: str = field(default = "Google")
    job_description: str = ""
    interview_type: InterviewType = field(default = InterviewType.MIXED)
    experience_level: ExperienceLevel = field(default = ExperienceLevel.MID)
    interview_duration: int = field(default = 30)
    max_questions: int = field(default = 8)
    voice_analysis_enabled: bool = field(default = False)
    voice_feedback: Optional[str] = field(default = None)
    interview_id: Optional[str] = None

__all__ = [
    "State",
]
