# Error Experiences and Known Issues

When working on this LINE Bot project using CHRLINE, be aware of the following known issues, error patterns, and API quirks.

## 1. Session Idle Timeout (Code 8: `V3_TOKEN_CLIENT_LOGGED_OUT`) & Auto-Recovery
- **Symptom:** The bot runs normally for roughly 2.5 hours and then suddenly gets forced out with a `V3_TOKEN_CLIENT_LOGGED_OUT` (Code 8) error.
- **Root Cause:** This is an **idle timeout** enforced by LINE's servers. A single Access Token session/connection has a hard lifespan of ~2-3 hours before the server terminates it.
- **The Old (Wrong) Solution:** We used to run a `proactive_refresh` thread every 2 hours to get a new token *before* the crash. **This is an anti-pattern.** Calling `refreshAccessToken` does NOT extend the lifespan of the *current* blocking connection (e.g. `cl.sync()`). It just gets a new token while the old connection still dies 30 minutes later. Worse, it triggers the API cooldown, which blocks the script from refreshing when it actually crashes!
- **The Correct Solution:** Delete `proactive_refresh` entirely. Let the script crash! When `Code 8` occurs, catch it in the main loop's `except Exception` block, identify it via `diagnose_error`, and call `cl.refreshAccessToken()`. **The Refresh Token remains fully valid even after the Access Token's session dies.** The bot will instantly fetch a new Access Token, rebuild the connection, and recover in milliseconds with zero downtime.

## 2. Token Refresh Loops
- **Symptom:** The bot spams the LINE servers with refresh attempts every few seconds.
- **Root Cause:** A bug in the old `auth.py` where the cooldown timer (`LAST_REFRESH_TIME`) was only updated upon a *successful* refresh. If a refresh failed, it would retry immediately.
- **Solution:** Always update the cooldown timestamp *before* making the API call (at the top of the `try` block). 

## 3. CHRLINE API Versioning & Breaking Changes
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
- **Solution:** Never use brute-force MID extraction for executing actions. Explicitly extract ONLY the `memberMids` and `inviteeMids` dictionaries from `chat['extra']`. Execute `deleteOtherFromChat` for members, and `cancelChatInvitation` for invitees.

## 14. Suicide/Self-Targeting Loop
- **Symptom:** If `TARGET_NAME` is configured to the bot's own name, the bot will infinitely attempt to ban itself.
- **Root Cause:** A bot cannot kick itself using `deleteOtherFromChat` (it must use `leaveGroup`). Thus, the kick fails silently, and the bot continues to detect itself in every sweep.
- **Solution:** Always implement a self-protection check: fetch the bot's own MID via `cl.profile.mid`, and explicitly `continue` or `return` if the target MID matches the bot's MID in `actions.py` and `bot.py`.
