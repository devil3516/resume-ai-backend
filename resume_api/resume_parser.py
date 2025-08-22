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

def ats_extractor(resume_data, model=model):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = '''
    You are an AI bot designed to act as a professional for parsing resumes. You are given a resume data and your job is to extract the following information:
    - name
    - email
    - phone
    - linkedin (if available)
    - github (if available)
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
        - Links: Github, or any live link ( if available)
    - certifications (if available): list of certifications with
        - name (certification name)
        - issuer (certification issuer)
        - issue_date (if available)
        - and pursuiing (if available)
    - awards (if available): list of awards with
        - name (award name)
        - description (award description)
        - year (award year) 

    
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







