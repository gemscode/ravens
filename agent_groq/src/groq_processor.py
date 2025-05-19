# agent_groq/src/groq_processor.py
import json
import logging
import re
from groq import Groq
from agent_core.interfaces.config import AppConfig

config = AppConfig()
logger = logging.getLogger(__name__)

class GroqProcessor:
    def __init__(self):
        self.client = Groq(api_key=config.grok_api_token)
    
    def analyze_resume(self, raw_text: str) -> dict:
        """Analyze resume text and return structured data"""
        try:
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",  # Updated model
                messages=[{
                    "role": "system",
                    "content": """Extract resume sections as VALID JSON with this structure:
                    {
                        "professional_experience": [{
                            "company": "Company Name",
                            "position": "Job Title",
                            "duration": "MM/YYYY - MM/YYYY",
                            "technologies": ["Tech1", "Tech2"],
                            "achievements": ["Achievement 1", "Achievement 2"]
                        }],
                        "education": [{
                            "institution": "University Name",
                            "degree": "Degree Earned",
                            "field_of_study": "Field/Major"
                        }],
                        "technical_skills": {
                            "languages": ["Python", "Java"],
                            "frameworks": ["React", "Spring"],
                            "tools": ["Docker", "Kubernetes"]
                        }
                    }
                    Output ONLY valid JSON, no markdown or extra text."""
                }, {
                    "role": "user",
                    "content": raw_text
                }],
                temperature=0.3,
                max_tokens=2048,
                response_format={"type": "json_object"}  # Enforce JSON mode
            )
            
            return self._parse_groq_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Groq analysis failed: {str(e)}")
            raise

    def _parse_groq_response(self, response_text: str) -> dict:
        """Convert Groq response text to structured JSON"""
        try:
            # Remove markdown code blocks and whitespace
            clean_text = re.sub(r'``````', '', response_text).strip()
            
            # Parse and validate JSON structure
            parsed = json.loads(clean_text)
            
            if not all(key in parsed for key in ('professional_experience', 'education', 'technical_skills')):
                raise ValueError("Missing required fields in Groq response")
                
            return parsed
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Groq response: {str(e)}")
            logger.debug(f"Raw response: {response_text}")  # For debugging
            return {"error": f"Invalid response format: {str(e)}"}

