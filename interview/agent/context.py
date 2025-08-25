"""Define the runtime context information for the agent."""

import os
from dataclasses import dataclass, field, fields
from typing_extensions import Annotated

from langchain_groq import ChatGroq   # if you're using Groq
 # if OpenAI
from langchain_anthropic import ChatAnthropic  # if Anthropic
from langgraph.checkpoint.sqlite import SqliteSaver  # <-- for memory
from enum import Enum
import interview.agent.prompts as prompts

class InterviewType(Enum):
    """The type of interview to conduct."""
    Technical = "technical"
    Behavioral = "behavioral"
    Mixed = "mixed"

class ExperienceLevel(Enum):
    """The experiance level of the candidate."""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    PRINCIPAL = "principal"


@dataclass(kw_only=True)
class Context:
    """Main context class for the memory graph system."""

    user_id: str = "default"
    """The ID of the user to remember in the conversation."""

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="groq/llama3-8b-8192",
        metadata={
            "description": "The name of the language model to use for the agent. "
            "Should be in the form: provider/model-name."
        },
    )

    system_prompt: str = prompts.SYSTEM_PROMPT
    db_path: str = "interview_agent.db"
    """The path to the database file."""

    job_title: str = field(default = "Software Engineer")
    """The title of the job."""

    company: str = field(default = "Google")
    """The company the job is at."""

    job_description: str = field(default = "")
    """The description of the job."""

    interview_type: InterviewType = field(default = InterviewType.Mixed)
    """The type of interview to conduct."""

    experience_level: ExperienceLevel = field(default = ExperienceLevel.MID)
    """The experiance level of the candidate."""
    
    interview_duration: int = field(default = 30)
    """The duration of the interview in minutes."""

    voice_analysis_enabled: bool = field(default = False)
    """Whether voice analysis is enabled for the interview."""

    interview_id: str = field(default = "default_interview_id")
    """The id of the interview."""


    def __post_init__(self):
        """Set default values if not provided."""
        # Convert string values to enums if needed
        if isinstance(self.interview_type, str):
            self.interview_type = InterviewType(self.interview_type.lower())
        if isinstance(self.experience_level, str):
            self.experience_level = ExperienceLevel(self.experience_level.lower())
        
        # Ensure numeric values are integers
        if isinstance(self.interview_duration, str):
            self.interview_duration = int(self.interview_duration)

    def get_llm(self):
        """Return the correct LLM instance based on the model string."""
        if self.model.startswith("groq/"):
            # Example: groq/llama3-8b-8192
            return ChatGroq(
                model=self.model.split("/", 1)[1],
                api_key=os.environ.get("GROQ_API_KEY")
            )
        else:
            raise ValueError(f"Unsupported model provider in {self.model}")
        
    def get_checkpointer(self):
        """Return a SqliteSaver instance for memory presistance"""
        return SqliteSaver.from_conn_string(self.db_path)
