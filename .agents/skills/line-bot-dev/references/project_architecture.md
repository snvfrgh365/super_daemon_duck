# Project Architecture & Decoupling

This bot (Super Daemon Duck) is structured to ensure that logic is properly decoupled, making it easier for AI models to maintain and debug.

## Core Principles
1. **Separation of Concerns:** Do not cram all logic into `bot.py`. Use specific modules for specific tasks.
2. **Robust Error Handling:** Always catch API exceptions gracefully, log them using the centralized logger, and attempt recovery (like token refresh) without crashing the main loop.
3. **Continuous Logging:** Log files are the primary way to debug session deaths and bugs. Ensure all critical actions and errors are logged using the structured tools in `logger.py`.

## Module Layout

- **`bot.py` (Main Loop & Entry Point)**
  - Responsible for initializing the CHRLINE client and running the main `while True` loop to listen for operations (`sync`).
  - Spawns background threads for continuous tasks: `background_sweep` (periodic group checks) and `proactive_refresh` (keeping the session alive).
  - Routes operations (like someone joining a group) to the appropriate action handlers.
  
- **`logger.py` (Logging & Diagnostics)**
  - Contains the entire logging infrastructure.
  - Implements rotating file handlers (logs are stored in the `logs/` directory).
  - Provides three distinct loggers: `sys_log` (general info), `error_log` (warnings/errors), and `action_log` (bans, kicks, radar events).
  - **Important:** Contains error diagnosis logic (`diagnose_error`, `ERROR_REASONS`). Do not put parsing/formatting logic in `bot.py`. Keep it here.

- **`auth.py` (Authentication & Refresh)**
  - Manages the lifecycle of the LINE tokens.
  - Contains `try_startup_refresh` and `try_refresh_token`.
  - Implements cooldowns to prevent spamming the LINE API if refreshing fails.

- **`actions.py` (Bot Actions)**
  - Contains the logic for interacting with users and groups (e.g., kicking, banning, sweeping groups).
  - Called by `bot.py` when a specific event occurs.

- **`dashboard.py` (UI/Status)**
  - Responsible for printing the status report to the terminal.
  - Contains safe dict getters (`safe_get`) used throughout the app to prevent `KeyError`s when dealing with undocumented LINE API responses.

- **`config.py` (Settings)**
  - Contains all constants: intervals, target names, file paths.
  - If a number or string is hardcoded, it likely belongs here.

- **`get_token.py` (Manual Auth)**
  - A standalone script used by the human operator to scan a QR code and generate a fresh `session_token.txt` and `refresh_token.txt`.

## Maintenance Rules for AI Agents
- When adding a new feature, decide carefully which file it belongs in. Don't just dump everything in `bot.py`.
- If an API response changes, update `dashboard.py` or the parsing logic where it's used.
- When you discover a new error pattern or fix a major bug, document it in `error_experiences.md`.
