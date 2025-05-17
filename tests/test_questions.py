# tests/test_questions.py
import pytest
import json
import hashlib
from app.services.questions import generate_questions
from tests.mocks import mock_openai, SAMPLE_QUESTIONS


@pytest.mark.asyncio
async def test_generate_questions(mock_openai):
    """Test generating questions using the mocked OpenAI API."""
    questions, bonus_question, questions_hash = await generate_questions()

    # Check that we got the expected questions
    assert len(questions) == len(SAMPLE_QUESTIONS)
    assert bonus_question is not None

    # Check that the hash was generated correctly
    game_data = {
        "questions": [q.model_dump() for q in questions],
        "bonus_question": bonus_question.model_dump() if bonus_question else None
    }
    expected_hash = hashlib.sha256(json.dumps(game_data, sort_keys=True).encode()).hexdigest()
    assert questions_hash == expected_hash
