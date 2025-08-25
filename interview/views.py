from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import uuid
import asyncio
import json
from .agent import create_app
from typing import Dict, Optional
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny

from .agent.state import State, InterviewType, ExperienceLevel


def _extract_last_message_content(messages):
    if not messages:
        return ""
    last = messages[-1]
    if hasattr(last, "content"):
        return last.content or ""
    if isinstance(last, dict):
        return last.get("content", "")
    return str(last)

class MockInterviewSystem:
    def __init__(self, db_path="interview_memory.db"):
        self.db_path = db_path
        self.app = create_app(self.db_path)
        self.active_users: Dict[str, str] = {}
        
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
        if not user_id:
            user_id = str(uuid.uuid4())
        interview_id = str(uuid.uuid4())

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
            "voice_analysis_enabled": voice_analysis,
            "interview_id": interview_id,
        }

        config = {"configurable": {"thread_id": interview_id}}
        result = await self.app.ainvoke(initial_state, config=config)

        result["user_id"] = user_id
        result["interview_id"] = interview_id
        self.active_users[user_id] = interview_id
        return result
    
    async def respond_to_question(self, user_id: str, response: str):
        if user_id not in self.active_users:
            raise ValueError(f"No active interview found for user {user_id}")

        config = {"configurable": {"thread_id": self.active_users[user_id]}}
        state = await self.app.aget_state(config)

        updated_state = {
            **state.values,
            "user_response": response,
            "current_state": "evaluate_response",
        }

        result = await self.app.ainvoke(updated_state, config=config)
        return result
    
    async def get_interview_status(self, user_id: str):
        if user_id not in self.active_users:
            return {"active": False}

        config = {"configurable": {"thread_id": self.active_users[user_id]}}
        state = await self.app.aget_state(config)

        return {
            "active": True,
            "question_count": state.values.get("question_count", 0),
            "max_questions": state.values.get("max_questions", 8),
            "current_state": state.values.get("current_state", "unknown"),
            "job_title": state.values.get("job_title", ""),
            "company": state.values.get("company", ""),
            "interview_type": state.values.get("interview_type", "").value if hasattr(state.values.get("interview_type"), "value") else "",
            "experience_level": state.values.get("experience_level", "").value if hasattr(state.values.get("experience_level"), "value") else "",
        }
    
    async def end_interview(self, user_id: str):
        if user_id in self.active_users:
            del self.active_users[user_id]
        return {"status": "ended", "user_id": user_id}
    
interview_system = MockInterviewSystem()

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def start_interview(request):
    if not interview_system:
        return Response({
            "error": "Interview agent not initialized. Please try again later."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        data = json.loads(request.body)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(interview_system.start_interview(
            job_title=data.get('job_title', 'Software Engineer'),
            company=data.get('company', 'TechCorp'),
            job_description=data.get('job_description', ''),
            interview_type=data.get('interview_type', 'mixed'),
            experience_level=data.get('experience_level', 'mid'),
            duration=data.get('duration', 30),
            voice_analysis=data.get('voice_analysis', False)
        ))
        loop.close()

        return Response({
            'user_id': result.get('user_id', str(uuid.uuid4())),
            'interview_id': result.get('interview_id'),
            'message': _extract_last_message_content(result.get('messages', [])),
            'interview_started': True,
            'max_questions': result.get('max_questions', 8)
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def response_to_question(request):
    if not interview_system:
        return Response({
            "error": "Interview agent not initialized. Please try again later."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        response = data.get('response','')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(interview_system.respond_to_question(user_id, response))
        loop.close()

        response_data = {
            'message': _extract_last_message_content(result.get('messages', [])),
            'question_count': result.get('question_count', 0),
            'max_questions': result.get('max_questions', 8),
        }
        if result.get('voice_feedback'):
            response_data['voice_feedback'] = result['voice_feedback']
        
        return Response(response_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def interview_status(request, user_id):
    if not interview_system:
        return Response({
            "error": "Interview agent not initialized. Please try again later."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        status_obj = loop.run_until_complete(interview_system.get_interview_status(user_id))
        loop.close()

        return Response(status_obj)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
