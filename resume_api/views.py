from django.shortcuts import render
import os
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from pypdf import PdfReader
from .resume_parser import ats_extractor, match_analyzer, generate_cover_letter
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
from django.utils import timezone
from .models import Resume



@api_view(['GET'])
@permission_classes([AllowAny])
def index(request):
    """Health check endpoint"""
    return Response({
        "message": "Resume Parser API is running successfully!",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "health": "/",
            "auth": {
                "login": "/api/auth/login/",
                "register": "/api/auth/register/",
                "logout": "/api/auth/logout/"
            },
            "resume": {
                "process": "/api/resumes/process/",
                "match": "/api/resumes/match/"
            }
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def process_resume(request):
    """Process uploaded PDF resume and extract information"""
    
    # Check if file was uploaded
    if 'pdf_doc' not in request.FILES:
        return Response(
            {"error": "No file part"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['pdf_doc']
    
    # Check if file has a name
    if uploaded_file.name == '':
        return Response(
            {"error": "No selected file"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if file is a PDF
    if not uploaded_file.name.lower().endswith('.pdf'):
        return Response(
            {"error": "File must be a PDF"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Create media directory if it doesn't exist
        media_dir = os.path.join(settings.MEDIA_ROOT, 'resumes')
        os.makedirs(media_dir, exist_ok=True)
        
        # Save the uploaded file
        file_path = os.path.join(media_dir, 'temp_resume.pdf')
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Read the PDF file
        data = _read_file_from_path(file_path)
        
        # Parse the resume
        parsed_data = ats_extractor(data)
        
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return Response(parsed_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Clean up the temporary file in case of error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        return Response(
            {"error": "Failed to process file", "message": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _read_file_from_path(path):
    """Extract text from PDF file"""
    reader = PdfReader(path)
    data = ""
    for page in reader.pages:
        data += page.extract_text()
    return data


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
def match_analysis(request):
    """Analyze how well a resume matches a job description"""
    
    try:
        data = request.data
        
        # Validate required fields
        if 'resume_data' not in data or 'job_description' not in data:
            return Response(
                {"error": "Both resume_data and job_description are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resume_data = data['resume_data']
        job_description = data['job_description']
        
        # Perform match analysis using LLM
        match_result = match_analyzer(resume_data, job_description)
        
        return Response(match_result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": "Failed to analyze match", "message": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    



@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
def save_resume(request):
    try:
        resume_data = request.data.get('resume_data')
        filename = request.data.get('original_filename', 'resume.pdf')
        
        # Save to your Resume model
        resume = Resume.objects.create(
            user=request.user,
            resume_data=resume_data,
            original_filename=filename,
            created_at=timezone.now()
        )
        
        return Response({'message': 'Resume saved successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=400)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_resume(request):
    try:
        latest_resume = Resume.objects.filter(user=request.user).latest('created_at')
        return Response({'resume_data': latest_resume.resume_data})
    except Resume.DoesNotExist:
        return Response({'message': 'No resume found'}, status=404)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume_history(request):
    resumes = Resume.objects.filter(user=request.user).order_by('-created_at')
    resume_list = []
    
    for resume in resumes:
        resume_list.append({
            'id': resume.id,
            'original_filename': resume.original_filename,
            'created_at': resume.created_at,
            'resume_data': resume.resume_data
        })
    
    return Response({'resumes': resume_list})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cover_letter_generator_custom(request):
    try:
        data = request.data
        resume_data = data.get('resume_data')
        job_description = data.get('job_description')
        company_name = data.get('company_name')
        job_title = data.get('job_title')
        additional_prompts = data.get('additional_prompts')

        #Generate Cover Letter with llm
        cover_letter = generate_cover_letter(resume_data, job_description, company_name, job_title, additional_prompts)
        return Response({'cover_letter': cover_letter})
    except Exception as e:
        return Response({'error': str(e)}, status=400)
        
        
        
