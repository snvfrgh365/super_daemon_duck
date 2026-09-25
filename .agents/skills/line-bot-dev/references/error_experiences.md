# Error Experiences and Known Issues

When working on this LINE Bot project using CHRLINE, be aware of the following known issues, error patterns, and API quirks.

## 1. Session Idle Timeout (Code 8: `V3_TOKEN_CLIENT_LOGGED_OUT`) & Auto-Recovery
- **Symptom:** The bot runs normally for roughly 3 hours and then suddenly gets forced out with a `V3_TOKEN_CLIENT_LOGGED_OUT` (Code 8) error. After that, attempts to call `refreshAccessToken` fail with `Code 1000, Message 2`.
- **Root Cause:** A single Access Token session/connection has a hard lifespan of ~2.5 to 3 hours before the server terminates it. **CRITICAL FINDING:** LINE's V3 Auth strictly prohibits calling `refreshAccessToken` AFTER the session has already been terminated (`Code 8`). If you wait for the session to die before requesting a new token, the server will reject your Refresh Token request with `Code 1000` (INVALID_GRANT) because the underlying E2EE connection/session is already marked as dead.
- **The Solution (Proactive Refresh):** You **must** run a `proactive_refresh` thread that calls `auth.try_refresh_token(cl)` every 2.5 hours, *before* the 3-hour expiry. This safely exchanges the Refresh Token for a new Access Token while the old connection is still valid. Then, when the old connection finally dies 30 minutes later (`Code 8`), the main thread will catch the exception, verify the token is already fresh, and simply rebuild the `cl.sync()` connection using the new Access Token, achieving a seamless recovery.

## 2. Token Refresh Loops & 24-Hour Bans (Anti-Spam)
- **Symptom:** The bot spams the LINE servers with refresh attempts, or the user gets hit with a `Code 1000` (invalid refresh token) and a 24-hour IP/account ban (`Code 100` / `Code 4`).
- **Root Cause 1 (Cooldowns):** A bug in old code where the cooldown timer was only updated upon a *successful* refresh. If a refresh failed, it would retry immediately.
- **Root Cause 2 (Forced Boot Refresh):** Attempting to forcefully call `refreshAccessToken` every time the bot boots up. Because developers restart the bot frequently during debugging, this spams the server and triggers a permanent 24-hour ban on the account/IP.
- **Root Cause 3 (Unsaved Test Refreshes):** If you write a temporary script to test `refreshAccessToken` but forget to save the returned tokens back to `tokens/`, the LINE server will invalidate your old tokens. Your main bot will then crash because the tokens on its disk are now dead.
- **Solution:** 
  1. Always update the cooldown timestamp *before* making the API call (at the top of the `try` block). 
  2. **NEVER** implement a "Forced Boot Refresh". The bot should simply boot using the existing Access Token.
  3. **ALWAYS** save the new `accessToken` and `refreshToken` back to the disk file the exact moment you receive them from `refreshAccessToken`.
- **Symptom:** Functions you try to call from the [Old API Reference](./chrline_old_api.md) raise exceptions like `AttributeError`, "fetchOps not found", or return entirely different data structures.
- **Root Cause:** LINE API is completely undocumented officially, and CHRLINE is a reverse-engineered library. The API changes frequently. For example, `fetchOps` was deprecated/removed by LINE and replaced by `sync`.
- **Solution:** 
  - Be prepared to fallback or find alternative methods.
  - E.g., in `bot.py`, we now use `cl.sync(cl.revision)` instead of `cl.fetchOps`.
  - Always check the latest CHRLINE source code or catch exceptions gracefully if a method signature changes.

## 4. Handling `CHRLINE.__init__` Validation Errors
- **Symptom:** When a token expires, instantiating `CHRLINE(token)` raises an error immediately, making it hard to call `refreshAccessToken` because you can't even build the client object.
- **Root Cause:** `CHRLINE.__init__` establishes a connection and then tries to validate the token. If the token is dead, it throws.
- **Solution:** In `auth.py`, we monkey-patch `CHRLINE.__init__` temporarily to suppress the validation exception. This allows the transport layer to be built, so we can then use the half-broken client object to call `refreshAccessToken`.

## 5. 403 Forbidden on Login (Device Spoofing)
- **Symptom:** Getting a `403 Forbidden` error when trying to generate a token or log in.
- **Root Cause:** LINE officially blocks certain default CHRLINE device characteristics on their server-side.
- **Solution:** Spoof the device characteristics in the `CHRLINE` constructor. Testing has shown that `device="DESKTOPMAC", version="8.4.1.3286", os_name="MAC", os_version="12.0"` has a higher success rate. If MAC fails, `device="IOSIPAD", version="13.4.0", os_name="iOS", os_version="16.0.0"` is a strong alternative.

## 6. Chat V2 API Migration (`kickoutFromGroup` errors)
- **Symptom:** Calling `kickoutFromGroup(group_id, target_mid)` raises `TalkService.kickoutFromGroup() takes 1 positional argument but 3 were given` or similar signature errors.
- **Root Cause:** LINE has migrated group management to the "Chat V2" API. Old TalkService RPC methods are either deprecated or their method signatures have changed drastically in the underlying Thrift definitions.
- **Solution:** Use the new Chat V2 methods instead:
  - To kick a member: `cl.deleteOtherFromChat(group_id, target_mid)` (or `[target_mid]` depending on the exact CHRLINE version).
  - To cancel an invitation: `cl.cancelChatInvitation(group_id, target_mid)`
  *(Note: The old `findAndAddContactsByMid` is also dead/deprecated, rely purely on `blockContact` -> `deleteOtherFromChat` for the ban sequence.)*

## 7. Continuous Logging for the Next Model
- As the bot evolves, whenever you encounter a new LINE API error code, unexpected ban, or token issue, **document it here**. 
- Always ensure the `logger.py` diagnosis logic (`_diagnose_error`) is updated when a new error code is discovered so that future logs are human-readable.

## 8. False Positive Login (Code 100 / Code 1 / Code 4)
- **Symptom:** You scan the QR code, enter the PIN, and your phone displays a push notification saying "Login successful (Mac/iPad)". However, the terminal immediately crashes with `Code: 100 (暫時無法進行認證)`, `Code: 1`, or `Code: 4`, and no token is generated.
- **Root Cause:** The account or IP is in a security cooldown (often due to previous spamming or bot-like behavior). LINE allows the primary auth (PIN) to pass, but the server firewall kicks the connection when CHRLINE attempts the secondary E2EE key exchange.
- **Solution:** Stop trying immediately (further attempts will worsen the ban). Either change your network IP (e.g., use a mobile hotspot) or wait 12-24 hours for the server cooldown to reset. Modifying code cannot bypass this server-side block.

## 9. Incomplete Event Polling in Secondary Mode (Delayed Bans)
- **Symptom:** The bot does not react instantly (in milliseconds) to someone joining a group. It only takes action when the periodic dashboard updates.
- **Root Cause:** The bot operates in `cmode: SECONDARY`. LINE servers often filter out or fail to push group membership change events (Op 13, 17, 124, 130) via `cl.sync()` to secondary devices, as they assume the primary mobile device handles them.
- **Solution:** Do not rely solely on `cl.sync()` for group defense. The `active_sweep` polling loop (which actively queries `getAllChatMids` -> `getChats(withMembers=True)` -> `getContacts` every 3-5 seconds) is mandatory to guarantee target detection.

## 10. Unvalidated Integer Types from API Responses (Crashes)
- **Symptom:** The bot crashes with `write() argument must be str, not int` in `auth.py`, or similar type errors when fetching contacts in `bot.py` or logging.
- **Root Cause:** CHRLINE's `checkAndGetValue` and the `ops` (operations) array often return integer error codes or timestamps when a request fails or when Thrift improperly assumes a type. If you assume `accessToken`, `refreshToken`, or `mid` are always strings, passing an integer to `f.write()` or `cl.getContact()` will cause a hard crash.
- **Solution:** Always validate that tokens are strings using `isinstance(token, str)` before saving. For MIDs extracted from ops (like `joined_mid` or `invited_mids`), explicitly cast them to strings `str(mid)` before passing them into other CHRLINE API methods like `getContact` or `deleteOtherFromChat`, and check for `None` to prevent passing `"None"`.

## 11. `safe_get` Fallback Trap on Empty Lists (`[]`)
- **Symptom:** `dashboard.py` or `actions.py` iterates over integer keys (e.g., `1`, `2`) instead of actual MIDs, crashing or returning empty "Unknown" groups, even when the bot is in 0 groups.
- **Root Cause:** The LINE server might return empty lists (e.g., `getAllChatMids()` -> `{1: [], 2: []}`). Using `gids = safe_get(chat_res, 'memberChatMids', 1) or chat_res` triggers the `or chat_res` fallback because Python treats an empty list `[]` as falsy. As a result, the script falls back to parsing the parent dictionary `{1: [], 2: []}`, treating the dictionary keys `1` and `2` as group IDs!
- **Solution:** Never use `or fallback` when extracting potentially empty lists or dicts from Thrift payloads. Always use explicit `is None` checks:
  ```python
  gids = safe_get(chat_res, 'memberChatMids', 1)
  if gids is None:
      gids = chat_res
  ```

## 12. `getProfile()` Returns a Parsed Dictionary, Not a Thrift List
- **Symptom:** Code expecting a Thrift object uses `checkAndGetValue(profile, "displayName", 20)` but gets `None`, making it seem like the API call failed or the Token is invalid.
- **Root Cause:** Unlike other CHRLINE APIs that return raw Thrift tuples/lists, `cl.getProfile()` returns a completely parsed Python dictionary with integer keys (e.g., `{1: 'mid...', 20: 'displayName...'}`).
- **Solution:** Do not use `checkAndGetValue()` on the `getProfile()` response. Directly access the dictionary using integer keys:
  ```python
  profile = cl.getProfile()
  name = profile.get(20) if isinstance(profile, dict) else "未知"
  ```

## 13. Phantom Ban Infinite Loop (Metadata Brute-forcing)
- **Symptom:** The bot infinitely spams "Target Found!" and "Kicked target!" in the logs for a specific user, but the user is not actually in the group's member list on your phone.
- **Root Cause:** If you use a brute-force scanner (like `extract_all_user_mids`) that blindly extracts any 33-char `u`-prefixed string from the `Chat` Thrift payload, you will accidentally extract the MIDs of the chat's creator, or people who were previously invited/kicked, because their MIDs remain embedded in the chat's historical metadata. The bot then attempts to kick them. Since they aren't members, `cl.deleteOtherFromChat()` fails silently on the server, causing the bot to retry infinitely in the next sweep.
- **Solution:** Never use brute-force MID extraction for executing actions. Explicitly extract ONLY the `memberMids` (key 4) and `inviteeMids` (key 5) dictionaries from `chat['extra']['groupExtra']` (key 8 -> key 1). Execute `deleteOtherFromChat` for members, and `cancelChatInvitation` for invitees.

## 14. Suicide/Self-Targeting Loop
- **Symptom:** If `TARGET_NAME` is configured to the bot's own name, the bot will infinitely attempt to ban itself.
- **Root Cause:** A bot cannot kick itself using `deleteOtherFromChat` (it must use `leaveGroup`). Thus, the kick fails silently, and the bot continues to detect itself in every sweep.
- **Solution:** Always implement a self-protection check: fetch the bot's own MID via `cl.profile.mid`, and explicitly `continue` or `return` if the target MID matches the bot's MID in `actions.py` and `bot.py`.

## 15. Silent Crash on Missing Config Property in Daemon Mode
- **Symptom:** The bot starts, logs "✅ 登入成功！", but never prints "主迴圈監聽中...". The dashboard freezes at an old timestamp, and the background process silently dies without outputting any python exception to `error.log`.
- **Root Cause:** A module (e.g., `services/uid_db.py`) imports a config property (e.g., `config.UID_DB_FILE`) that was never defined in `core/config.py`. Since this import happens in the main thread (during early boot/dashboard drawing) *before* the `try/except` loop of `background_sweep` starts, it triggers an `AttributeError` that kills the entire script silently in `nohup` mode.
- **Solution:** Always meticulously double-check that every variable referenced across decoupled files actually exists in the central `config.py`.

## 16. Log Tailing Failure with TimedRotatingFileHandler
- **Symptom:** `scripts/see.sh` fails to display the latest action or system logs, always showing "尚無任何紀錄" even though the Python process is actively logging.
- **Root Cause:** Python's `TimedRotatingFileHandler` writes to the exact base filename (e.g., `action.log`) and only appends the date suffix (e.g., `action_2026-09-25.log`) during the midnight rollover. If bash scripts mistakenly `tail $(ls -t action_*.log)`, they will only grab *yesterday's* rolled-over log, completely missing today's active `action.log`.
- **Solution:** Bash monitoring scripts must tail the active base filename explicitly: `tail -n 5 logs/action/action.log`.

## 17. Absolute Equality vs Substring Matching in Python Sets
- **Symptom:** Target lists (like `target_names.txt`) seem to misbehave when dealing with invisible/whitespace characters.
- **Root Cause:** Python's `in` operator on a `set()` (e.g., `name in get_target_names()`) evaluates as *absolute equality* (O(1) hash collision), not a fuzzy substring match. However, if the text file is read using `line.strip()`, it forcibly removes intentional spaces (like `"張興華 "`). If `is_target()` also uses `name.strip()`, it alters the exact LINE API payload, potentially causing false positives or allowing targets to evade by padding spaces.
- **Solution:** When absolute accuracy is required, read the target list using `line.rstrip("\r\n")` to preserve user-intended trailing spaces, and do NOT apply `.strip()` to the incoming `name` payload from LINE.

## 18. Path Binding in Linux Background Scripts (Relative vs Absolute)
- **Symptom:** Scripts run perfectly when initiated from `~/good_line_bot/`, but crash or write files to strange directories when triggered via systemd, cron, or from another folder.
- **Root Cause:** Functions like `open("logs/dashboard.txt", "w")` use relative paths based on the Current Working Directory (CWD).
- **Solution:** All internal file references must be anchored to an absolute `BASE_DIR` computed dynamically:
  ```python
  BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  os.path.join(BASE_DIR, "logs", "dashboard.txt")
  ```
