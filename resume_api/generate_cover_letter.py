import os
import re
import json
from dotenv import load_dotenv
import requests

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
model = "llama3-70b-8192"

def clean_json_string(s):
    # Remove trailing commas before } or ]
    s = re.sub(r",\s*([}\]])", r"\1", s)
    # Remove markdown formatting
    s = re.sub(r"^```(json)?", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"```$", "", s).strip()
    return s



def generate_cover_letter(resume_data=None, job_description=None, company_name=None, job_title=None, additional_prompts=None, model=model):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Handle optional resume_data
    resume_section = ""
    if resume_data:
        resume_section = f"🧾 Resume Data:\n{resume_data}\n"
    else:
        resume_section = "🧾 Resume Data: Not provided - write a general but professional cover letter\n"

    prompt = f'''
    You are an expert career coach and professional writer.
    Write a customized, concise, and compelling cover letter for the following job application.
    
    {resume_section}
    
    📄 Job Description:
    {job_description}
    
    🏢 Company Name:
    {company_name}
    
    🎯 Job Title:
    {job_title}
    
    💬 Additional Instructions or Custom Prompts:
    {additional_prompts or "None provided"}
    
    ---
    ✍️ CRITICAL INSTRUCTIONS:
    - DO NOT add any preamble, introduction text, or explanatory text
    - DO NOT say "Here is a cover letter for..." or similar phrases
    - Start DIRECTLY with the cover letter content
    - Begin with "Dear Hiring Manager" or appropriate salutation
    - Write ONLY the cover letter content, nothing else
    
    ✍️ Cover Letter Requirements:
    - Address the letter to the appropriate team or "Hiring Manager"
    - Keep it under 400 words
    - Use a professional but friendly tone
    - Focus on how the applicant's skills meet the role's needs
    - End with a call to action (e.g., request for interview or contact)
    - If no resume data is provided, write a general but professional cover letter that could be customized
    '''
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert career coach and professional writer. You write compelling, professional cover letters tailored to specific job applications. IMPORTANT: Output ONLY the cover letter content with no preamble, introduction, or explanatory text. Start directly with the salutation."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            return content
        else:
            return {"error": f"API request failed with status code {response.status_code}", "message": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "message": str(e)}
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON from response", "raw": response.text}