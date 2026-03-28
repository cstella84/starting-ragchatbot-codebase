import pytest


class TestQueryEndpoint:
    def test_returns_answer_and_sources(self, client, mock_rag):
        mock_rag.query.return_value = ("Python is a language.", [{"title": "Intro to Python"}])

        response = client.post(
            "/api/query",
            json={"query": "What is Python?", "session_id": "sess-abc"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Python is a language."
        assert data["sources"] == [{"title": "Intro to Python"}]
        assert data["session_id"] == "sess-abc"

    def test_passes_query_and_session_id_to_rag(self, client, mock_rag):
        client.post("/api/query", json={"query": "Tell me about ML", "session_id": "s1"})

        mock_rag.query.assert_called_once_with("Tell me about ML", "s1")

    def test_creates_session_when_none_provided(self, client, mock_rag):
        mock_rag.session_manager.create_session.return_value = "auto-session"
        mock_rag.query.return_value = ("Answer.", [])

        response = client.post("/api/query", json={"query": "Any question"})

        assert response.status_code == 200
        assert response.json()["session_id"] == "auto-session"
        mock_rag.session_manager.create_session.assert_called_once()

    def test_missing_query_field_returns_422(self, client, mock_rag):
        response = client.post("/api/query", json={"session_id": "sess-abc"})

        assert response.status_code == 422

    def test_rag_exception_returns_500(self, client, mock_rag):
        mock_rag.query.side_effect = Exception("Vector DB unavailable")

        response = client.post("/api/query", json={"query": "Any question"})

        assert response.status_code == 500
        assert "Vector DB unavailable" in response.json()["detail"]


class TestCoursesEndpoint:
    def test_returns_course_stats(self, client, mock_rag):
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": ["Python 101", "ML Basics", "Data Engineering"],
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 3
        assert data["course_titles"] == ["Python 101", "ML Basics", "Data Engineering"]

    def test_empty_catalog(self, client, mock_rag):
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_analytics_exception_returns_500(self, client, mock_rag):
        mock_rag.get_course_analytics.side_effect = Exception("ChromaDB error")

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert "ChromaDB error" in response.json()["detail"]


class TestClearSessionEndpoint:
    def test_clears_session_successfully(self, client, mock_rag):
        response = client.post("/api/session/clear", json={"session_id": "sess-xyz"})

        assert response.status_code == 200
        assert response.json() == {"success": True}
        mock_rag.session_manager.clear_session.assert_called_once_with("sess-xyz")

    def test_missing_session_id_returns_422(self, client, mock_rag):
        response = client.post("/api/session/clear", json={})

        assert response.status_code == 422

    def test_clear_exception_returns_500(self, client, mock_rag):
        mock_rag.session_manager.clear_session.side_effect = Exception("Session not found")

        response = client.post("/api/session/clear", json={"session_id": "missing"})

        assert response.status_code == 500
        assert "Session not found" in response.json()["detail"]
