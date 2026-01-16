# PRD: Fix Frontend-Backend Connection in Docker

## Introduction

The frontend container is unable to connect to the backend service's `/chat` endpoint, resulting in a "connection failed" error. However, accessing the backend from the host machine works. This task aims to diagnose the networking or configuration mismatch and implement a fix so the containerized frontend can communicate with the backend.

## Goals

- Enable the frontend container to successfully make HTTP requests to the Backend container.
- Ensure `BACKEND_URL` environment variable is correctly propagated and used (Investigation + Fix).
- Verify end-to-end chat functionality in Docker Compose.

## User Stories

### US-001: Standardize Backend URL Configuration
**Description:** As a developer, I want the frontend to consistently use the `BACKEND_URL` environment variable so that it can point to `http://backend:8000` inside Docker and `http://localhost:8000` locally.

**Acceptance Criteria:**
- [ ] Frontend `app.py` reads `BACKEND_URL` (defaults to `http://localhost:8000` if missing).
- [ ] Docker Compose `frontend` service has `BACKEND_URL` set to the backend service alias (e.g. `http://backend:8000`).
- [ ] Frontend logs the configured backend URL on startup (for debugging).
- [ ] Typecheck passes.

### US-002: Verify Docker Networking
**Description:** As a user, I want to be able to chat via the frontend in Docker without connection errors.

**Acceptance Criteria:**
- [ ] `docker-compose up` starts both services without error.
- [ ] Sending a message in the frontend results in a streaming response from the backend.
- [ ] No "Connection refused" or "Name resolution" errors in frontend logs.
- [ ] Verify in browser using dev-browser skill (open http://localhost:8501).

## Functional Requirements

- FR-1: Frontend must respect `BACKEND_URL` env var.
- FR-2: Docker Compose must define the internal service network alias for the backend.

## Non-Goals

- Changing the backend API contract.
- Adding authentication.

## Success Metrics

- Zero connection errors in frontend logs during a chat session.
- Successful message echo/response in the UI.

## Open Questions

- Is there a proxy or firewall in the container image? (Assuming standard python/slim images).
