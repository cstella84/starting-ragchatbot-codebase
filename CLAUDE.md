# [CLAUDE.md](http://CLAUDE.md)

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Setup:**

```bash
cp .env.example .env   # add ANTHROPIC_API_KEY
uv sync                # install dependencies
```

**Run the app:**

```bash
./run.sh
# or
cd backend && uv run uvicorn app:app --reload --port 8000
```

**Run a one-off Python script in the backend:**

```bash
cd backend && uv run python <script.py>
```

Always use `uv` to run Python — never use `pip` or `python` directly.

There are no tests or linting configured.

## Architecture

The app is a RAG chatbot that answers questions about course materials using semantic search + Claude AI. The backend is a FastAPI server (`backend/`) that also serves the static frontend (`frontend/`).

**Key flow for a user query:**

1. Frontend POSTs to `/api/query` with `{query, session_id}`
2. `RAGSystem.query()` assembles conversation history and calls Claude
3. Claude invokes the `search_course_content` tool → `CourseSearchTool` → `VectorStore.search()` (ChromaDB)
4. Tool results are returned to Claude, which synthesizes the final answer
5. Sources and response are returned; session history is updated

**Core modules in `backend/`:**


| File                    | Role                                                                                              |
| ----------------------- | ------------------------------------------------------------------------------------------------- |
| `app.py`                | FastAPI entrypoint; serves frontend; loads `docs/` on startup                                     |
| `rag_system.py`         | Orchestrator — wires all components together                                                      |
| `vector_store.py`       | ChromaDB abstraction; dual collections: `course_catalog` (metadata) and `course_content` (chunks) |
| `document_processor.py` | Parses `.txt`/`.pdf`/`.docx` course files; chunks text with overlap                               |
| `ai_generator.py`       | Anthropic API wrapper; manages tool-calling loop                                                  |
| `search_tools.py`       | `CourseSearchTool` + `ToolManager`; tracks sources per query                                      |
| `session_manager.py`    | Per-session conversation history (capped at `MAX_HISTORY` exchanges)                              |
| `config.py`             | All tunable constants (`CHUNK_SIZE`, `MAX_RESULTS`, model names, etc.)                            |


**Course document format** (files in `docs/`):

```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 0: <lesson title>
Lesson Link: <url>
<lesson content>

Lesson 1: ...
```

`document_processor.py` uses regex to parse this structure. Adding a new course is as simple as dropping a correctly formatted `.txt` file in `docs/` and restarting the server (startup deduplicates by course title).

**ChromaDB** is stored at `backend/chroma_db/` and persists across restarts. To force a full rebuild, delete that directory before starting.

**Configuration** lives entirely in `backend/config.py` and is driven by environment variables (only `ANTHROPIC_API_KEY` is required).