# app/services/questions.py
import hashlib
import json
from typing import List, Tuple, Optional
from openai import AsyncOpenAI  # Use AsyncOpenAI
from ..config import settings
from ..schemas import Question

# Create async client instance
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_questions(num_questions: int = 15) -> Tuple[List[Question], Optional[Question], str]:
    """
    Generate questions using OpenAI with increasing difficulty and hints
    Returns: (regular_questions, bonus_question, hash)
    """

    prompt = f"""
    Generate {num_questions} trivia questions for a 'Who Wants to Be a Millionaire' style game, plus 1 bonus question.

    IMPORTANT: 1. Regular questions MUST be in INCREASING difficulty, starting with easy questions and ending with 
    very difficult ones. 2. The bonus question should be of MEDIUM difficulty (around the middle level of the regular 
    questions).

    Format as a JSON object with a "questions" array for the regular questions and a "bonus_question" object:
    {{
        "questions": [
            {{
                "q": "Question text here?",
                "correct": "The correct answer",
                "wrong": ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"],
                "hint": "A helpful hint about the question that gives a clue without revealing the answer directly"
            }}, 
            // more questions in increasing difficulty...
        ],
        "bonus_question": {{
            "q": "Bonus question text here?",
            "correct": "The correct answer",
            "wrong": ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"],
            "hint": "A helpful hint about this bonus question"
        }}
    }}

    Make sure questions cover a variety of topics and knowledge areas.
    """

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are a helpful assistant that generates increasingly difficult trivia questions in JSON "
                        "format."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    # Extract the content and parse JSON
    content = response.choices[0].message.content
    data = json.loads(content)
    questions_data = data.get("questions", [])
    bonus_question_data = data.get("bonus_question")

    # Convert to Pydantic models (without difficulty field)
    questions = [Question.model_validate(q) for q in questions_data]
    bonus_question = Question.model_validate(bonus_question_data) if bonus_question_data else None

    # Create deterministic hash for replay
    game_data = {
        "questions": [q.model_dump() for q in questions],
        "bonus_question": bonus_question.model_dump() if bonus_question else None
    }

    questions_hash = hashlib.sha256(json.dumps(game_data, sort_keys=True).encode()).hexdigest()

    return questions, bonus_question, questions_hash
