import json
import hashlib
import textwrap
from typing import List, Optional, Tuple, Union, Any

from fastapi import HTTPException
from openai import AsyncOpenAI
from pydantic import ValidationError

from ..config import settings
from ..schemas import Question

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def update_game_questions(
        existing_data: dict,
        admin_prompt: str
) -> Tuple[List[Question], Optional[Question], str]:
    """
    Given the current quiz JSON and an admin instruction, ask the AI
    to modify the questions according to the game rules and return
    (questions, bonus_question, new_hash).
    """
    # 1) Build a system message that encapsulates game context and constraints
    system_msg = textwrap.dedent("""
        You are an expert 'Who Wants to Be a Millionaire?' question writer and editor.  
        Each quiz consists of 15 multiple-choice questions of ascending difficulty (1–15) and prize tiers ("$100" up 
        to "$1,000,000"), plus an optional medium-difficulty bonus question.  
        When updating:
        - Preserve the overall structure: count, difficulties, prize tiers, and category distribution.
        - Follow the Question schema exactly: each question object must include:
          • "q": question text with a reasoning or puzzle element
          • "correct": correct answer string
          • "wrong": exactly three plausible distractors
          • "hint": a genuine 50/50 clue that helps but does not hand it away
          • "difficulty": integer 1–15 (maintain monotonic progression)
          • "category": one of [History, Geography, Science, Arts & Literature, Sports, Pop Culture, Food & Drink, 
          Nature, Tech & Innovation, World Cultures]
          • "prize": string representing the tier (e.g. "$100", ..., "$1,000,000")
        - Ensure any new or modified wrong answers remain contextually plausible.
        - Apply the administrator's instructions precisely without introducing extraneous changes.
        Output exactly one JSON object with only these keys:
        {
          "questions": [ ... ],       // array of 15 question objects
          "bonus_question": { ... }  // a bonus question object or null
        }
        Do not include any commentary, markdown, or extra fields.
    """)

    # 2) Build a user message containing the current data and admin instructions
    payload = {
        "questions": existing_data.get("questions", []),
        "bonus_question": existing_data.get("bonus_question")
    }
    user_msg = textwrap.dedent(f"""
    Current quiz data:
    {json.dumps(payload, indent=2)}

    Admin instructions:
    {admin_prompt}

    Return only the updated JSON payload as specified.
    """)

    try:
        # 3) Call the AI
        resp = await client.chat.completions.create(
            model="gpt-4o",
            temperature=0.7,
            top_p=0.9,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"}
        )

        # 4) Extract and normalize the AI response
        raw: Union[str, Any] = resp.choices[0].message.content
        if isinstance(raw, str):
            try:
                new_data = json.loads(raw)
            except json.JSONDecodeError:
                raise HTTPException(status_code=502, detail="AI returned invalid JSON string for update")
        elif isinstance(raw, dict):
            new_data = raw
        else:
            raise HTTPException(status_code=502, detail="AI returned unexpected type for update payload")

        # 5) Validate with Pydantic
        questions = [Question.model_validate(q) for q in new_data["questions"]]
        bonus_q = (
            Question.model_validate(new_data.get("bonus_question"))
            if new_data.get("bonus_question") else None
        )

        # 6) Compute a new hash for idempotency
        canonical = {
            "questions": [q.model_dump() for q in questions],
            "bonus_question": bonus_q.model_dump() if bonus_q else None
        }
        new_hash = hashlib.sha256(
            json.dumps(canonical, sort_keys=True).encode()
        ).hexdigest()

        return questions, bonus_q, new_hash

    except ValidationError as ve:
        raise HTTPException(status_code=502, detail=f"Updated data failed validation: {ve}")
    except HTTPException:
        # re-raise HTTPExceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI update failed: {e}")
