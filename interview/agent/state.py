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
    """The messages in the conversation."""
    
    current_state: str = "start"
    """The current state of the conversation."""

    user_metadata: Dict[str, str] = field(default_factory=dict)
    """The metadata for the user."""

    conversation_memory: List[Dict[str, str]] = field(default_factory=list)
    """The memory of the conversation."""

    interview_started: bool = False
    """Whether the interview has started."""

    follow_up_needed: bool = False
    """Whether follow-up is needed."""

    interview_progress: int = 0
    """Progress of the interview."""
    
    current_question: Optional[str] = None
    """The current question being asked."""
    
    user_response: Optional[str] = None
    """The user's response to the current question."""
    
    question_count: int = 0
    """Number of questions asked so far."""
    
    job_title: str = "Software Engineer"
    """Job title being interviewed for."""
    
    company: str = "TechCorp"
    """Company being interviewed for."""
    
    job_description: str = ""
    """Job description for the position."""
    
    interview_type: InterviewType = InterviewType.MIXED
    """Type of interview: technical, behavioral, or mixed."""
    
    experience_level: ExperienceLevel = ExperienceLevel.MID
    """Experience level of the candidate."""
    
    interview_duration: int = 30
    """Interview duration in minutes."""
    
    max_questions: int = 8
    """Maximum number of questions based on duration."""
    
    voice_analysis_enabled: bool = False
    """Whether voice analysis is enabled."""
    
    voice_feedback: Optional[str] = None
    """Voice analysis feedback if enabled."""


__all__ = [
    "State",
]
