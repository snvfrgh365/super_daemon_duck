# auth.py
import os
import time
import config
from logger import sys_log, error_log

LAST_REFRESH_TIME = 0
REFRESH_COOLDOWN = 300  # 5 分鐘冷卻，避免短時間內瘋狂重試（原本 12 小時太長）


def _read_refresh_token():
    """讀取 Refresh Token 檔案，回傳 token 字串或 None。"""
    if not os.path.exists(config.REFRESH_TOKEN_FILE):
        error_log.error(f"找不到 {config.REFRESH_TOKEN_FILE}，無法續命")
        return None

    with open(config.REFRESH_TOKEN_FILE, "r") as f:
        refresh_token = f.read().strip()

    if not refresh_token:
        error_log.error("Refresh Token 檔案內容為空")
        return None

    return refresh_token


def _check_cooldown():
    """檢查冷卻時間，回傳 True 表示可以繼續，False 表示仍在冷卻中。"""
    global LAST_REFRESH_TIME
    current_time = time.time()
    elapsed = current_time - LAST_REFRESH_TIME

    if elapsed < REFRESH_COOLDOWN:
        remaining = int(REFRESH_COOLDOWN - elapsed)
        error_log.warning(f"續命冷卻中，{remaining} 秒後才能重試")
        return False
    return True


def _save_new_tokens(new_access_token, new_refresh_token=None):
    """將新的 Token 寫回檔案，確保下次開機也能用。"""
    os.makedirs(os.path.dirname(config.TOKEN_FILE) or ".", exist_ok=True)

    with open(config.TOKEN_FILE, "w") as f:
        f.write(new_access_token)

    if new_refresh_token:
        with open(config.REFRESH_TOKEN_FILE, "w") as f:
            f.write(new_refresh_token)
        sys_log.info("🔑 新的 Refresh Token 也已一併更新。")


def try_startup_refresh():
    """
    啟動時 Access Token 已失效的救援機制。
    不會觸發 QR Code 登入流程，完全自動。

    原理：CHRLINE 建構時會先建立連線通道，再驗證 Token。
    我們攔截驗證失敗的例外，保留已建立的連線，
    再用這條連線呼叫 refreshAccessToken 取得新 Token。
    """
    global LAST_REFRESH_TIME

    if not _check_cooldown():
        return None

    refresh_token = _read_refresh_token()
    if not refresh_token:
        return None

    # 讀取已過期的 Token（用於部分初始化 CHRLINE 的連線通道）
    if not os.path.exists(config.TOKEN_FILE):
        error_log.error(f"找不到 {config.TOKEN_FILE}")
        return None
    with open(config.TOKEN_FILE, "r") as f:
        expired_token = f.read().strip()
    if not expired_token:
        error_log.error("Session Token 檔案內容為空")
        return None

    try:
        sys_log.info("🔄 Token 已失效，正在用 Refresh Token 嘗試自動續命...")

        from CHRLINE import CHRLINE

        # ---- 核心手法 ----
        # CHRLINE.__init__ 流程：建立連線通道 → 驗證 Token → 驗證失敗拋例外
        # 我們暫時攔截這個例外，讓物件存活，保留已建好的連線通道。
        _original_init = CHRLINE.__init__

        def _init_suppress_login_error(self, *args, **kwargs):
            try:
                _original_init(self, *args, **kwargs)
            except Exception:
                pass  # 壓制 Token 驗證錯誤，連線通道已在例外前建立完成

        CHRLINE.__init__ = _init_suppress_login_error
        try:
            temp_cl = CHRLINE(
                expired_token,
                device="DESKTOPMAC",
                version="8.4.1.3286",
                os_name="MAC",
                os_version="12.0"
            )
        finally:
            CHRLINE.__init__ = _original_init  # 無論成敗都還原，不影響後續正常建構

        # 用保留下來的連線通道呼叫 refreshAccessToken
        RATR = temp_cl.refreshAccessToken(refresh_token)
        new_token = temp_cl.checkAndGetValue(RATR, "accessToken", 1)

        if not new_token:
            error_log.error("Refresh 回應為空，Refresh Token 可能也已過期，請重新掃碼")
            return None

        # 檢查是否有回傳新的 Refresh Token (有些版本的 API 會 rotate)
        new_refresh = temp_cl.checkAndGetValue(RATR, "refreshToken", 2)
        _save_new_tokens(new_token, new_refresh)

        LAST_REFRESH_TIME = time.time()
        sys_log.info("✅ 啟動續命成功！已取得新 Access Token。")
        return new_token

    except Exception as e:
        error_log.error(f"啟動續命失敗 (可能 Refresh Token 也已過期，請重新掃碼): {e}")
        return None


def try_refresh_token(cl):
    """
    運行中 Token 過期的續命機制。
    依賴已建立的 cl 物件，在原有連線上刷新 Token。
    """
    global LAST_REFRESH_TIME

    if not _check_cooldown():
        return False

    refresh_token = _read_refresh_token()
    if not refresh_token:
        return False

    try:
        # 先更新冷卻時間，無論成功失敗都進入冷卻，避免狂發請求被鎖
        LAST_REFRESH_TIME = time.time()
        
        sys_log.info("🔄 偵測到 Token 可能已過期，正在嘗試自動續命...")
        RATR = cl.refreshAccessToken(refresh_token)
        new_token = cl.checkAndGetValue(RATR, "accessToken", 1)

        if not new_token:
            error_log.error("Refresh 回應為空，Refresh Token 可能已過期，請重新掃碼")
            return False

        # 更新 cl 的 Token 並重建連線通道
        cl.authToken = new_token
        cl.handleNextToken(new_token)

        # 檢查是否有回傳新的 Refresh Token
        new_refresh = cl.checkAndGetValue(RATR, "refreshToken", 2)
        _save_new_tokens(new_token, new_refresh)

        sys_log.info("✅ Token 自動續命成功！壽命已延長。")
        return True

    except Exception as e:
        error_log.error(f"自動續命失敗 (可能 Refresh Token 已經過期，請重新掃碼): {e}")
    return False
