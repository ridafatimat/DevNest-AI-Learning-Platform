import os
import httpx
import json
from dotenv import load_dotenv
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Debug output
print(f"🔑 [ai_client.py] OPENAI_API_KEY loaded: {bool(OPENAI_API_KEY)}")

# Your prompt template
PROMPT_TEMPLATE = """
You are an AI reviewing a code submission.

Language: {language}

Content:
{content}

Return a JSON with:
- summary (string): A brief summary of the code
- issues (array of strings): List of problems or bugs found
- suggestions (array of strings): List of improvement recommendations
- confidence (number between 0 and 1): Your confidence in the review
- modelVersion (string): The AI model used
"""


def call_openai(prompt: str):
    """Call OpenAI API"""
    if not OPENAI_API_KEY:
        print("⚠️ [ai_client.py] No OpenAI key found")
        return None
    
    print(f"✅ [ai_client.py] Calling OpenAI API with model: gpt-4o-mini")
    
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a code review assistant. Always respond with valid JSON only, no markdown code blocks or extra text."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            },
            timeout=30
        )
        
        resp.raise_for_status()
        response_data = resp.json()
        text = response_data["choices"][0]["message"]["content"]
        
        # Clean markdown code blocks if present
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            result = json.loads(text)
            # Ensure all required fields are present
            if "modelVersion" not in result:
                result["modelVersion"] = "gpt-4o-mini"
            print(f"✅ [ai_client.py] Successfully got OpenAI response")
            return result
        except json.JSONDecodeError as e:
            print(f"⚠️ [ai_client.py] Failed to parse OpenAI JSON: {e}")
            print(f"Raw response: {text[:200]}...")
            return {
                "summary": text[:500] if len(text) > 0 else "Unable to parse AI response",
                "issues": [],
                "suggestions": [],
                "confidence": 0.3,
                "modelVersion": "gpt-4o-mini-fallback"
            }
    except httpx.HTTPStatusError as e:
        print(f"❌ [ai_client.py] OpenAI API HTTP error: {e.response.status_code}")
        if e.response.status_code == 429:
            print("⚠️ [ai_client.py] Rate limit hit - create a new OpenAI key or add payment")
        return None
    except Exception as e:
        print(f"❌ [ai_client.py] OpenAI API error: {str(e)}")
        return None


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
def call_ai(prompt: str):
    """
    Try OpenAI, fallback to mock data
    """
    # Try OpenAI
    result = call_openai(prompt)
    if result:
        return result
    
    # Return mock data if OpenAI fails
    print("⚠️ [ai_client.py] OpenAI failed, returning mock data")
    return {
        "summary": "Mock summary - AI Review temporarily unavailable",
        "issues": ["Mock issue - Configure OPENAI_API_KEY or add payment"],
        "suggestions": ["Mock suggestion - Add valid OpenAI API key to enable real AI reviews"],
        "confidence": 0.5,
        "modelVersion": "mock-v1"
    }


def review_code(submission):
    """Review code submission"""
    print(f"📝 [ai_client.py] Reviewing code in language: {submission['language']}")
    prompt = PROMPT_TEMPLATE.format(
        language=submission["language"],
        content=submission["code"]
    )
    return call_ai(prompt)


def explain_question(question: str):
    """Explain a coding question"""
    prompt = f"""
    Explain this coding question in a simple, easy-to-understand way.
    
    Question:
    {question}

    Return ONLY valid JSON with this structure:
    {{
        "explanation": "your clear explanation here",
        "modelVersion": "model-name"
    }}
    """
    return call_ai(prompt)


def generate_study_plan(topic: str):
    """Generate a 7-day study plan"""
    prompt = f"""
    Create a detailed 7-day study plan for learning: {topic}

    Return ONLY valid JSON with this structure:
    {{
        "topics": ["topic1", "topic2", "topic3"],
        "schedule": [
            "Day 1: Introduction and basics",
            "Day 2: Core concepts",
            "Day 3: Practical examples",
            "Day 4: Advanced topics",
            "Day 5: Project work",
            "Day 6: Review and practice",
            "Day 7: Assessment and next steps"
        ],
        "modelVersion": "model-name"
    }}
    """
    return call_ai(prompt)