# New Chat Button — Design Spec

**Date:** 2026-03-27

## Context

The RAG chatbot sidebar has no way to start a fresh conversation without reloading the page. Users who want to ask about a new topic are stuck with the existing session history influencing Claude's responses. Adding a "New Chat" button lets users reset cleanly — clearing the UI and freeing the backend session memory.

## What We're Building

A `+ NEW CHAT` button in the left sidebar, positioned above the Courses section. Clicking it clears the conversation, resets the session on the backend, and starts fresh — no page reload required.

## UI & Styling

`**frontend/index.html`**

- Add a new `<div class="sidebar-section">` above the existing courses section
- Contains a single `<button class="new-chat-btn">+ NEW CHAT</button>`

`**frontend/style.css**`

- Add `.new-chat-btn` with:
  - Text: `font-size: 0.875rem`, `font-weight: 600`, `color: var(--text-secondary)`, `text-transform: uppercase`, `letter-spacing: 0.5px` — matches `.stats-header` / `.suggested-header`
  - Border: `1px solid var(--border-color)`, `border-radius: 6px`, `padding: 6px 12px`
  - Layout: `background: transparent`, `cursor: pointer`, `width: 100%`
  - Hover: `border-color: var(--primary-color)`, `color: var(--primary-color)` — matches `.suggested-item` hover pattern

## Frontend Behavior

`**frontend/script.js**`

- Add click handler on `.new-chat-btn`:
  1. If `currentSessionId` is not null, call `POST /api/session/clear` with `{ session_id: currentSessionId }` (fire and forget)
  2. Set `currentSessionId = null`
  3. Call existing `createNewSession()` to clear the chat UI and show the welcome message

## Backend

`**backend/app.py**`

- Add `POST /api/session/clear` endpoint
- Request body: `{ session_id: str }`
- Calls `rag_system.session_manager.clear_session(session_id)`
- Returns `{ "success": true }`
- If session_id does not exist: silently no-ops (no error)

`**backend/session_manager.py**`

- No changes — `clear_session(session_id)` already exists

## Files to Modify


| File                  | Change                                                                   |
| --------------------- | ------------------------------------------------------------------------ |
| `frontend/index.html` | Add new-chat button in sidebar above courses section                     |
| `frontend/style.css`  | Add `.new-chat-btn` styles                                               |
| `frontend/script.js`  | Add click handler calling `/api/session/clear` then `createNewSession()` |
| `backend/app.py`      | Add `POST /api/session/clear` endpoint                                   |


## Verification

1. Start the app: `./run.sh`
2. Send a few messages in the chat
3. Click `+ NEW CHAT` in the sidebar
4. Confirm: chat window clears and shows welcome message
5. Confirm: sending a new message gets a fresh response with no history bleed-through
6. Confirm: the button hover state matches the sidebar's existing hover style

