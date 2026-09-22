---
name: line-bot-dev
description: >-
  Use this skill when developing, debugging, or maintaining the Super Daemon Duck LINE bot based on the CHRLINE library. It provides crucial context on project architecture, error handling, and historical LINE API quirks.
---

# Super Daemon Duck (LINE Bot) Development Guide

This project is a LINE Bot built on top of the reverse-engineered `CHRLINE` library. Because the official LINE API is heavily restricted and undocumented for normal users, this bot uses a desktop client emulator (DESKTOPMAC) to interact with LINE.

When working on this project, the model MUST consult this skill to understand how the project is structured and what historical issues we have faced.

## Important References

Before making architectural changes or debugging complex issues, read the following:

1. **[Project Architecture & Decoupling](./references/project_architecture.md)**: 
   Read this to understand where code belongs (e.g., `logger.py` vs `bot.py` vs `auth.py`). Do not cram everything into `bot.py`.
2. **[Error Experiences & Known Issues](./references/error_experiences.md)**:
   Read this when dealing with `CHRLINE` exceptions, token refresh bugs, session timeouts (like the infamous 3-hour timeout), and API versioning changes.
3. **[Old CHRLINE API Reference](./references/chrline_old_api.md)**:
   A legacy dump of the old CHRLINE API endpoints. Use this as a rough reference for what the library *might* support, but be aware that method names and signatures often change as LINE updates its servers.

## Development Rules

1. **Continuous Documentation:** Whenever you solve a complex bug related to the LINE API, or discover a new behavior (like a new timeout limit or error code), you **must** update `error_experiences.md` to help the next model.
2. **Centralized Logging:** All errors must be routed through `logger.py`. If a new LINE API error code is discovered, update `ERROR_REASONS` and `diagnose_error` in `logger.py` so logs remain human-readable.
3. **Safe API Access:** CHRLINE methods often return nested arrays or dictionaries without clear keys. Always use `safe_get` (from `dashboard.py`) to extract data from API responses to prevent `KeyError` or `IndexError` crashes.
