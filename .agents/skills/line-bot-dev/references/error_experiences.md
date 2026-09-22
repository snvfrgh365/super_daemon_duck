# Error Experiences and Known Issues

When working on this LINE Bot project using CHRLINE, be aware of the following known issues, error patterns, and API quirks.

## 1. Session Idle Timeout (Code 8: `V3_TOKEN_CLIENT_LOGGED_OUT`)
- **Symptom:** The bot runs normally for roughly 3 hours and then suddenly gets forced out with a `V3_TOKEN_CLIENT_LOGGED_OUT` (Code 8) error.
- **Root Cause:** This is often not because of a banned account, but an **idle timeout** on the session enforced by LINE's servers. The session dies if it's not refreshed.
- **Solution:** We implemented a `proactive_refresh` thread in `bot.py` that refreshes the access token every 2 to 2.5 hours randomly (`config.PROACTIVE_REFRESH_MIN` and `MAX`).
- **Debugging Note:** Never rely on the token surviving forever just because its stated lifespan is 30 days. The *session* is much shorter.

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
- **Solution:** Spoof the device characteristics in the `CHRLINE` constructor. Testing has shown that `device="DESKTOPMAC", version="8.4.1.3286", os_name="MAC", os_version="12.0"` has a higher success rate of bypassing the block.

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
