from django.shortcuts import render
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from pypdf import PdfReader
from .resume_parser import ats_extractor, match_analyzer
from django.conf import settings


@api_view(['GET'])
def index(request):
    """Health check endpoint"""
    return Response({"message": "Resume Parser API is running."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
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
