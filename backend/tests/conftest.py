import pytest
from unittest.mock import MagicMock, patch

# Patch RAGSystem and StaticFiles *before* app.py is first imported so that:
#   - RAGSystem() constructor never touches ChromaDB or the Anthropic API
#   - StaticFiles() never tries to access the ../frontend directory
_rag_instance = MagicMock()

with patch("rag_system.RAGSystem", return_value=_rag_instance), \
     patch("fastapi.staticfiles.StaticFiles", return_value=MagicMock()):
    from app import app  # noqa: E402 – intentional deferred import

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def mock_rag():
    """Reset the shared RAGSystem mock before each test and return it."""
    _rag_instance.reset_mock()
    # Sensible defaults so tests that don't override these still get valid responses
    _rag_instance.session_manager.create_session.return_value = "generated-session-id"
    _rag_instance.query.return_value = ("Default answer.", [])
    _rag_instance.get_course_analytics.return_value = {
        "total_courses": 0,
        "course_titles": [],
    }
    return _rag_instance


@pytest.fixture
def client(mock_rag):
    """Return a TestClient backed by the FastAPI app with RAGSystem mocked."""
    return TestClient(app)
