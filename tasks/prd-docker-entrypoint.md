# PRD: Docker Entrypoint Secret Injection

## Introduction

A shell script to serve as a Docker ENTRYPOINT. Its purpose is to bridge the gap between Docker Secrets (files) and legacy applications that expect Environment Variables. It reads files from a secrets directory, injects them as environment variables, and then executes the main application command.

## Goals

-   Enable legacy applications to consume Docker Secrets as environment variables.
-   Ensure the main application runs as PID 1 (using `exec`).
-   Handle missing secret directories gracefully.
-   Ensure clean values by stripping trailing whitespace.

## User Stories

### US-001: Create Entrypoint Script
**Description:** As a DevOps engineer, I want a `bash` entrypoint script that reads files from `/run/secrets/`, exports them as environment variables (filename=KEY, content=VALUE), strips trailing whitespace, and then executes the command passed to the container.

**Acceptance Criteria:**
-   [ ] Script uses `#!/bin/bash` interpreter.
-   [ ] Checks if `/run/secrets/` directory exists.
    -   If missing: Log a warning message (e.g., "Secrets directory found, skipping injection") and continue.
    -   If present: Proceed to processing.
-   [ ] Iterates through every file in the secrets directory.
-   [ ] For each file:
    -   Key = Filename.
    -   Value = File content, with all trailing whitespace/newlines stripped.
    -   Export as Environment Variable.
-   [ ] Executes the passed command using `exec "$@"` to ensure the application runs as PID 1.
-   [ ] Typecheck/lint passes (shellcheck if available, or manual verification).
-   [ ] Verify locally (e.g., mock secrets dir and run script).

## Functional Requirements

-   **FR-1:** The script must use `bash`.
-   **FR-2:** The script must check for the existence of `/run/secrets/`.
-   **FR-3:** If the secrets directory is missing, the script must log a warning to stderr and proceed without error.
-   **FR-4:** The script must loop through all files in the secrets directory.
-   **FR-5:** The script must read each file's content and strip any trailing newline characters or whitespace.
-   **FR-6:** The script must process `exec "$@"` as the final step to launch the command provided as arguments.

## Non-Goals

-   Recursive directory traversal (top-level files only).
-   Complex decoding of secret values (assume plain text).
-   Filtering or mapping of secret names (direct 1:1 mapping from filename to env var name).

## Technical Considerations

-   **Whitespace Handling:** Bash command substitution `$(cat file)` inherently strips trailing newlines, which is desired behavior here.
-   **Execution:** Using `exec` is critical for signal propagation (SIGTERM/SIGINT) to the application.

## Success Metrics

-   Application starts successfully.
-   Application has access to secrets via `os.environ` or `getenv`.
-   No "zombie" processes (PID 1 handling).

## Open Questions

-   None. (Clarified: Bash, Strip Whitespace, Permissive Failure).
