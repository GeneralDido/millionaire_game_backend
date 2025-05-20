# app/services/questions.py
import hashlib
import json
import textwrap
from typing import List, Tuple, Optional

from fastapi import HTTPException
from openai import AsyncOpenAI  # Use AsyncOpenAI
from pydantic import ValidationError

from ..config import settings
from ..schemas import Question

# Create async client instance
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_questions(num_questions: int = 15) -> Tuple[List[Question], Optional[Question], str]:
    """
    Generate questions using OpenAI with increasing difficulty and hints
    Returns: (regular_questions, bonus_question, hash)
    """

    prompt = textwrap.dedent(f"""
        You are an expert Who Wants to Be a Millionaire question writer.  
        Generate {num_questions} unique multiple-choice questions PLUS a single bonus question, with realistic 
        ascending prize tiers.

        Output exactly one JSON object with keys:
        - "questions": array of {num_questions}
        - "bonus_question": object

        Each question must have:
          • "difficulty": integer 1–15 (monotonic: 1–5 easy, 6–10 medium, 11–15 hard)
          • "prize": string, the money amount (e.g. "$100", ..., "$1,000,000")
          • "category": one of [History, Geography, Science, Arts & Literature,
                                Sports, Pop Culture, Food & Drink,
                                Nature, Tech & Innovation, World Cultures]
          • "q": question text (requires ≥1 inference step or mini-puzzle)
          • "correct": the correct answer
          • "wrong": array of three plausible but subtly incorrect answers
          • "hint": a genuine 50/50 clue that’s helpful but doesn’t hand it away

        Strict constraints: 1. No “trivia-101” topics: avoid capitals, ‘first president’, standard rivers/mountains, 
        monarch names, famous paintings/artists. 2. Use scenario, data-interpretation, or multi-step logic questions 
        whenever possible. 3. No more than two questions per category. 4. Bonus must be difficulty 8–10, prize tier 
        around the “$16,000–$32,000” level. 5. Wrong answers must be factually plausible within the question’s context.

        Example “hard” format for inspiration: “During WWII, codebreakers at Bletchley Park named one of their 
        machines after a local fruit. What was it called and what cipher did it tackle?” """)

    try:
        # 1) call the API
        resp = await client.chat.completions.create(
            model="gpt-4o",
            temperature=0.8,
            top_p=0.9,
            messages=[
                {"role": "system", "content": (
                    "You are an expert 'Who Wants to Be a Millionaire?' question writer."
                )},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        # 2) parse the string payload to a Python dict
        payload = resp.choices[0].message.content
        data = json.loads(payload)

        # 3) convert into Pydantic models (can raise ValidationError)
        questions = [Question.model_validate(q) for q in data["questions"]]
        bonus_q = (
            Question.model_validate(data["bonus_question"])
            if data.get("bonus_question")
            else None
        )

        # 4) build the hash
        game_data = {
            "questions": [q.model_dump() for q in questions],
            "bonus_question": bonus_q.model_dump() if bonus_q else None
        }
        questions_hash = hashlib.sha256(
            json.dumps(game_data, sort_keys=True).encode()
        ).hexdigest()

        return questions, bonus_q, questions_hash

    except json.JSONDecodeError:
        raise HTTPException(502, "OpenAI returned invalid JSON")
    except ValidationError as ve:
        raise HTTPException(502, f"Malformed question schema: {ve}")
    except HTTPException:
        # re-raise our own HTTPExceptions untouched
        raise
    except Exception as e:
        # catch *everything* else and turn it into JSON
        raise HTTPException(503, f"Question generation failed: {e}")
