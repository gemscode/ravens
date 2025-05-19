from langchain import Groq
import json

def process_resume_pdf(file_path):
    # Extract text from PDF
    text_content = extract_pdf_text(file_path)
    
    # Create structured extraction prompt
    prompt = """Extract the following from the resume:
    - companies: list of company names with periods
    - projects: list of projects with client names
    - education: educational background
    - technologies: list of technologies used
    - titles: job titles held
    Format as JSON."""
    
    # Process with Groq
    client = Groq()
    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt + text_content}],
        temperature=0
    )
    
    return json.loads(response.choices[0].message.content)
