# interview-agent/interview_system.py
"""Main interview system for Django integration."""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from langgraph.runtime import Runtime
from langgraph.store.sqlite import SqliteStore

from .context import Context, InterviewType, ExperienceLevel
from .graph import interview_graph


class MockInterviewSystem:
    def __init__(self, db_path="interview_memory.db"):
        self.store = SqliteStore.from_conn_string(db_path)
        self.active_interviews: Dict[str, Runtime] = {}
        
    async def start_interview(
        self, 
        user_id: Optional[str] = None,
        job_title: str = "Software Engineer",
        company: str = "TechCorp",
        job_description: str = "",
        interview_type: str = "mixed",
        experience_level: str = "mid",
        duration: int = 30,
        voice_analysis: bool = False
    ):
        """Start a new interview session with custom configuration."""
        if not user_id:
            user_id = str(uuid.uuid4())
            
        # Create context with user-provided values
        context = Context(
            user_id=user_id,
            db_path="interview_memory.db",
            job_title=job_title,
            company=company,
            job_description=job_description,
            interview_type=interview_type,
            experience_level=experience_level,
            interview_duration=duration,
            voice_analysis_enabled=voice_analysis
        )
        
        runtime = Runtime(
            graph=interview_graph,
            store=self.store,
            context=context
        )
        
        # Store the runtime for this interview
        self.active_interviews[user_id] = runtime
        
        # Initialize state with custom configuration
        initial_state = {
            "messages": [],
            "current_state": "start",
            "interview_started": False,
            "follow_up_needed": False,
            "interview_progress": 0,
            "question_count": 0,
            "job_title": job_title,
            "company": company,
            "job_description": job_description,
            "interview_type": InterviewType(interview_type),
            "experience_level": ExperienceLevel(experience_level),
            "interview_duration": duration,
            "voice_analysis_enabled": voice_analysis
        }
        
        # Run the graph
        config = {"configurable": {"thread_id": user_id}}
        result = await runtime.arun(initial_state, config=config)
        
        # Add user_id to result
        result["user_id"] = user_id
        return result
    
    async def respond_to_question(self, user_id: str, response: str):
        """Process user response and continue interview."""
        if user_id not in self.active_interviews:
            raise ValueError(f"No active interview found for user {user_id}")
            
        runtime = self.active_interviews[user_id]
        
        # Get current state
        config = {"configurable": {"thread_id": user_id}}
        current_state = await runtime.aget_state(config)
        
        # Update with user response
        updated_state = {
            **current_state.values,
            "user_response": response,
            "current_state": "evaluate_response"
        }
        
        # Continue the graph
        result = await runtime.arun(updated_state, config=config)
        return result
    
    async def get_interview_status(self, user_id: str):
        """Get the current status of an interview."""
        if user_id not in self.active_interviews:
            return {"active": False}
            
        runtime = self.active_interviews[user_id]
        config = {"configurable": {"thread_id": user_id}}
        state = await runtime.aget_state(config)
        
        return {
            "active": True,
            "question_count": state.values.get("question_count", 0),
            "max_questions": state.values.get("max_questions", 8),
            "current_state": state.values.get("current_state", "unknown"),
            "job_title": state.values.get("job_title", ""),
            "company": state.values.get("company", ""),
            "interview_type": state.values.get("interview_type", "").value if hasattr(state.values.get("interview_type"), "value") else "",
            "experience_level": state.values.get("experience_level", "").value if hasattr(state.values.get("experience_level"), "value") else ""
        }
    
    async def end_interview(self, user_id: str):
        """End an interview session."""
        if user_id in self.active_interviews:
            del self.active_interviews[user_id]
        return {"status": "ended", "user_id": user_id}