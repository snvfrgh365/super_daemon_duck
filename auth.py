# auth.py
import os
import time
import config
from logger import sys_log, error_log

LAST_REFRESH_TIME = 0

def try_refresh_token(cl):
    global LAST_REFRESH_TIME
    current_time = time.time()
    
    # 冷卻機制：如果距離上次續命不到 12 小時 (43200 秒)，則拒絕重複續命
    if current_time - LAST_REFRESH_TIME < 43200:
        return False

    if not os.path.exists(config.REFRESH_TOKEN_FILE):
        return False
    
    try:
        with open(config.REFRESH_TOKEN_FILE, "r") as f:
            refresh_token = f.read().strip()
        
        if not refresh_token: return False

        sys_log.info("🔄 [系統] 偵測到 Token 可能已過期，正在嘗試自動續命...")
        RATR = cl.refreshAccessToken(refresh_token)
        new_token = cl.checkAndGetValue(RATR, "accessToken", 1)
        
        if new_token:
            cl.authToken = new_token
            # 存回檔案，確保下次開機也是用新的
            with open(config.TOKEN_FILE, "w") as f:
                f.write(new_token)
            
            # CHRLINE 的防護機制：更新 Token 後必須重建連線通道
            cl.handleNextToken(new_token) 
            LAST_REFRESH_TIME = current_time
            sys_log.info("✅ [系統] Token 自動續命成功！壽命已延長 30 天。")
            return True
            
    except Exception as e:
        error_log.error(f"❌ [系統] 自動續命失敗 (可能 RefreshToken 已經過期，請重新掃碼): {e}")
    return False
