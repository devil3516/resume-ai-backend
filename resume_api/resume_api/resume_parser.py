import os
import re
import json
from dotenv import load_dotenv
import requests

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def clean_json_string(s):
    # Remove trailing commas before } or ]
    s = re.sub(r",\s*([}\]])", r"\1", s)
    # Remove markdown formatting
    s = re.sub(r"^```(json)?", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"```$", "", s).strip()
    return s

def ats_extractor(resume_data, model="llama3-70b-8192"):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = '''
    You are an AI bot designed to act as a professional for parsing resumes. You are given a resume and your job is to extract the following information:
    - name
    - email
    - phone
    - linkedin
    - address (if available)
    - portfolio (if available)
    - summary (2-3 sentence professional summary)
    - skills (as a list)
    - experience: list of work experience entries with
        - title (job title)
        - company
        - start_date (if available)
        - end_date (if available)
        - description (main bullet point or summary of experience)
    - education: list of education entries with
        - degree
        - university
        - graduation_year (if available)
    - projects: list of projects with
        - name (project name)
        - description (project description)
        - technologies (if available)
    
    Only return valid JSON. Ensure all strings are properly closed and formatted. Do not include trailing commas, incomplete objects, or markdown formatting.
    
    Resume text:
    \"\"\"{resume_data}\"\"\"
    '''

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that parses resumes into structured JSON data."},
            {"role": "user", "content": prompt.format(resume_data=resume_data)}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()

            # Try to isolate valid JSON block using regex
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                json_string = clean_json_string(match.group())

                try:
                    parsed_data = json.loads(json_string)
                    return parsed_data
                except json.JSONDecodeError as e:
                    return {"error": "Failed to parse JSON after cleaning", "raw": json_string, "message": str(e)}
            else:
                return {"error": "No valid JSON object found", "raw": content}

        else:
            return {"error": f"API request failed with status code {response.status_code}", "message": response.text}

    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "message": str(e)}

    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON from response", "raw": response.text}

def match_analyzer(resume_data, job_description, model="llama3-70b-8192"):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = '''
    You are an expert HR professional and resume analyzer. Your task is to analyze how well a candidate's resume matches a specific job description.

    Resume Data:
    {resume_data}

    Job Description:
    {job_description}

    You MUST return a JSON response with EXACTLY this structure (all fields are required):
    {{
        "overallMatch": <number between 0-100>,
        "skillsMatch": <number between 0-100>,
        "experienceMatch": <number between 0-100>,
        "educationMatch": <number between 0-100>,
        "missingKeywords": ["keyword1", "keyword2", ...],
        "recommendedImprovements": ["improvement1", "improvement2", ...]
    }}

    Guidelines for scoring:
    - overallMatch: Overall fit for the position (consider all factors)
    - skillsMatch: How well the candidate's skills align with job requirements (REQUIRED - must be included)
    - experienceMatch: How relevant the candidate's experience is to the role
    - educationMatch: How well the education background fits the requirements
    - missingKeywords: Important skills/technologies mentioned in job description but not found in resume
    - recommendedImprovements: Specific actionable suggestions to improve the resume for this job

    IMPORTANT: You MUST include ALL six fields in your response. Do not omit any fields.
    Only return valid JSON. Do not include any markdown formatting or additional text.
    '''

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert HR professional that analyzes resume-job matches and provides detailed scoring and recommendations."},
            {"role": "user", "content": prompt.format(resume_data=json.dumps(resume_data, indent=2), job_description=job_description)}
        ],
        "temperature": 0.1
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()

            # Try to isolate valid JSON block using regex
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                json_string = clean_json_string(match.group())

                try:
                    parsed_data = json.loads(json_string)
                    
                    # Validate and ensure all required fields are present
                    required_fields = ['overallMatch', 'skillsMatch', 'experienceMatch', 'educationMatch', 'missingKeywords', 'recommendedImprovements']
                    for field in required_fields:
                        if field not in parsed_data:
                            if field in ['overallMatch', 'skillsMatch', 'experienceMatch', 'educationMatch']:
                                parsed_data[field] = 0  # Default to 0 for missing scores
                            elif field in ['missingKeywords', 'recommendedImprovements']:
                                parsed_data[field] = []  # Default to empty array for missing lists
                    
                    return parsed_data
                except json.JSONDecodeError as e:
                    return {"error": "Failed to parse JSON after cleaning", "raw": json_string, "message": str(e)}
            else:
                return {"error": "No valid JSON object found", "raw": content}

        else:
            return {"error": f"API request failed with status code {response.status_code}", "message": response.text}

    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "message": str(e)}

    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON from response", "raw": response.text}
    



