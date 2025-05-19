import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from pdf2image import convert_from_path
import pytesseract
import json
from docx import Document
import re

load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')

def extract_text(file_path):
    """Extract text from different file types (PDF, DOCX, TXT)."""
    try:
        if file_path.endswith('.pdf'):
            images = convert_from_path(file_path)
            text_content = []
            for image in images:
                text = pytesseract.image_to_string(image)
                text_content.append(text)
            return "\n".join(text_content)
        elif file_path.endswith('.docx'):
            doc = Document(file_path)
            text_content = [paragraph.text for paragraph in doc.paragraphs]
            return "\n".join(text_content)
        elif file_path.endswith('.txt'):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
        else:
            return None
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return None

def verify_skill_in_resume(skill, resume_text):
    """Verify if a skill is actually mentioned in the resume text"""
    skill_terms = skill.lower().split()
    resume_lower = resume_text.lower()
    
    # Check for exact matches first
    if skill.lower() in resume_lower:
        return True
        
    # Check for individual terms (for multi-word skills)
    # Require at least half of the terms to be present
    if len(skill_terms) > 1:
        matches = sum(1 for term in skill_terms if term in resume_lower and len(term) > 3)
        return matches >= len(skill_terms) / 2
        
    return False

def validate_match_results(match_data, resume_text):
    """Validate that the match results are reasonable and based on actual resume content"""
    # Check if overall percentage is too high
    if match_data["match_percentage"] > 80:
        match_data["match_percentage"] = 80
    
    # Verify each skill is actually in the resume
    for match in match_data.get("top_matches", []):
        criterion = match["criterion"]
        # If skill isn't in resume, cap percentage at 10%
        if not verify_skill_in_resume(criterion, resume_text):
            match["percentage"] = min(match["percentage"], 10)
            
    # Recalculate total after verification
    total_criteria_percentage = sum(match["percentage"] for match in match_data["top_matches"])
    
    # If total is now less than match percentage, adjust overall percentage
    if total_criteria_percentage < match_data["match_percentage"]:
        match_data["match_percentage"] = total_criteria_percentage
    
    # Ensure percentages add up correctly
    if abs(total_criteria_percentage - match_data["match_percentage"]) > 1:  # Allow 1% rounding error
        # Normalize percentages
        factor = match_data["match_percentage"] / total_criteria_percentage if total_criteria_percentage > 0 else 0
        for match in match_data["top_matches"]:
            match["percentage"] = round(match["percentage"] * factor)
            
    return match_data

def calculate_match_percentage(resume_text, job_description, chat):
    """
    Analyzes the resume and job description to identify matching criteria and 
    calculate a match percentage. Returns the overall match percentage and the
    top matching criteria.
    """
    prompt = [HumanMessage(content=f"""
    Analyze this resume against the job description and provide a realistic matching assessment:

    1. First, identify the key required skills and qualifications from the job description.
    2. For each requirement, search the resume for EXPLICIT evidence of that skill or related experience.
    3. Assign a match percentage (0-40%) for each requirement based ONLY on what is explicitly mentioned in the resume.
    4. Calculate an overall match percentage between 0-60% that reflects the true alignment.
    5. Be extremely conservative - if a skill is not explicitly mentioned in the resume, the match should be 0% for that skill.
    6. The sum of individual percentages should equal the overall match percentage.
    7. You must quote the exact text from the resume that supports each match.

    Format your response as:
    {{
      "match_percentage": X,
      "top_matches": [
        {{"criterion": "Specific skill from job description", "percentage": Y, "evidence": "EXACT QUOTE from resume that proves this skill"}},
        {{"criterion": "Another skill from job description", "percentage": Z, "evidence": "EXACT QUOTE from resume that proves this skill"}},
        ...
      ]
    }}

    Resume:
    {resume_text}

    Job Description:
    {job_description}
    """)]

    try:
        response = chat.invoke(prompt)
        print("Raw API response:", response.content)  # Debug print
        
        # Try to extract JSON from the response content
        json_start = response.content.find('{')
        json_end = response.content.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = response.content[json_start:json_end]
            match_data = json.loads(json_str)
            
            # Remove evidence/explanation field for compatibility with existing code
            for match in match_data.get("top_matches", []):
                if "evidence" in match:
                    del match["evidence"]
                if "explanation" in match:
                    del match["explanation"]
                    
            # Validate and normalize the results
            match_data = validate_match_results(match_data, resume_text)
            return match_data
        else:
            print("Could not find valid JSON in the response")
            return {"match_percentage": 0, "top_matches": []}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {"match_percentage": 0, "top_matches": []}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"match_percentage": 0, "top_matches": []}


if __name__ == "__main__":
    resume_file = input("Enter path to resume file: ")
    job_description_file = input("Enter path to job description file: ")

    resume_text = extract_text(resume_file)
    job_description = extract_text(job_description_file)

    # Use Claude model for more accurate assessment
    chat = ChatGroq(
        api_key=groq_api_key,
        model_name="claude-3-opus-20240229"  # Using Claude 3 Opus for better accuracy
    )

    if resume_text and job_description:
        match_results = calculate_match_percentage(resume_text, job_description, chat)
        print(json.dumps(match_results, indent=4))
    else:
        print("Could not extract text from one or both files.")
