# tests/test_client_base.py
from typing import Generator
from fastapi.testclient import TestClient
from fastapi import FastAPI
import pytest

from app.main import app


class TestClientGenerator:
    """Class for generating test clients with ASGI support"""

    @staticmethod
    def get_test_client(_app: FastAPI) -> TestClient:
        """Get a synchronous TestClient for the provided FastAPI app"""
        return TestClient(_app)


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Get a synchronous test client"""
    with TestClient(app) as client:
        yield client
