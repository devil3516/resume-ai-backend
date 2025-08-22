from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import uuid
import asyncio
import json

try:
    from interview_agent.src.memory_agent.interview_system import MockInterviewSystem
except ImportError:
    # Fallback to absolute import if relative import fails
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'interview_agent', 'src'))
        from interview_agent.src.memory_agent.interview_system import MockInterviewSystem
    except ImportError:
        raise ImportError("Interview agent not found. Please ensure the interview-agent package is installed.")
MockInterviewSystem = None

interview_system = MockInterviewSystem() if MockInterviewSystem else None

@api_view(['POST'])
@csrf_exempt
def start_interview(request):
    """Start a mock interview."""
    if not interview_system:
        return Response({
            "error": "Interview agent not initialized. Please try again later."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        data = json.loads(request.body)
        
        #Start the interview using asyncio
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
            'message': result['messages'][-1]['content'],
            'interview_started': True,
            'max_questions': result.get('max_questions', 8)
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
@api_view(['POST'])
@csrf_exempt
def response_to_question(request):
    """Process a response to a question."""
    if not interview_system:
        return Response({
            "error": "Interview agent not initialized. Please try again later."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        response = data.get('response',"")
        
        #Process the response using asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(interview_system.response_to_question(user_id, response))
        loop.close()

        response_data = {
            'message':result['messages'][-1]['content'],
            'question_count':result.get('question_count', 0),
            'max_questions':result.get('max_questions', 8),
        }
        if result.get('voice_feedback'):
            response_data['voice_feedback'] = result['voice_feedback']
        
        return Response(response_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
@api_view(['POST'])
@csrf_exempt
def interview_status(request, user_id):
    """Get the current status of the interview."""
    if not interview_system:
        return Response({
            "error": "Interview agent not initialized. Please try again later."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        status = loop.run_until_complete(interview_system.get_interview_status(user_id))
        loop.close()

        return Response(status)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
