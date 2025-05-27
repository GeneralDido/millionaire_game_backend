# tests/mocks.py
import json
from unittest.mock import AsyncMock, patch
import pytest

from app.schemas import Question

# Sample questions for testing
SAMPLE_QUESTIONS = [
    Question(
        q="What is the capital of France?",
        correct="Paris",
        wrong=["London", "Berlin", "Madrid"],
        difficulty=1,
        category="Geography",
        hint="This city is known as the City of Light."
    ),
    Question(
        q="Which planet is known as the Red Planet?",
        correct="Mars",
        wrong=["Venus", "Jupiter", "Mercury"],
        difficulty=2,
        category="Science",
        hint="It's named after the Roman god of war."
    ),
]

SAMPLE_BONUS_QUESTION = Question(
    q="What is the largest mammal?",
    correct="Blue Whale",
    wrong=["Elephant", "Giraffe", "Hippopotamus"],
    difficulty=3,
    category="Biology",
    hint="It lives in the ocean."
)

# Mock OpenAI response
MOCK_OPENAI_RESPONSE = {
    "questions": [q.model_dump() for q in SAMPLE_QUESTIONS],
    "bonus_question": SAMPLE_BONUS_QUESTION.model_dump()
}


@pytest.fixture
def mock_openai():
    """Fixture to mock OpenAI API calls."""
    mock_client = AsyncMock()

    # Set up the mock response structure
    mock_completion = AsyncMock()
    mock_choice = AsyncMock()
    mock_message = AsyncMock()

    mock_message.content = json.dumps(MOCK_OPENAI_RESPONSE)
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_completion

    with patch('app.services.questions.client', mock_client):
        yield mock_client
