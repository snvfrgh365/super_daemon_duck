# logger.py
import logging
from logging.handlers import TimedRotatingFileHandler
import os

# 確保 logs 資料夾存在
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 共用輸出格式
formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 控制台專用設定 (顯示給人類看的)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

def create_logger(name, filename, level, retention_days):
    """建立帶有輪轉機制的 Logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重複綁定 handler
    if not logger.handlers:
        file_path = os.path.join(LOG_DIR, filename)
        
        # 每天午夜 (midnight) 輪轉一次檔案，保留 retention_days 天的備份
        file_handler = TimedRotatingFileHandler(
            filename=file_path,
            when="midnight",
            interval=1,
            backupCount=retention_days,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

# 1. 系統日常 Log (保留 7 天)
sys_log = create_logger("System", "system.log", logging.INFO, 7)

# 2. 錯誤 Log (保留 30 天，只記錄 WARNING 以上)
error_log = create_logger("Error", "error.log", logging.WARNING, 30)

# 3. 行動 Log (保留 30 天，紀錄所有封鎖、踢人、掃描行動)
action_log = create_logger("Action", "action.log", logging.INFO, 30)


# ============================================================
# 錯誤診斷工具
# ============================================================

# LINE 錯誤碼對照表
ERROR_REASONS = {
    8:    ("SESSION_LOGGED_OUT", "LINE server terminated session (idle timeout / another device login / security policy)"),
    1:    ("ILLEGAL_ARGUMENT", "Request format error, CHRLINE version may be incompatible"),
    3:    ("SERVER_INTERNAL_ERROR", "LINE server error, usually temporary"),
    20:   ("AUTH_FAILED", "Token rejected, possibly expired or revoked"),
    1000: ("AUTH_ERROR", "Auth-related error, refresh token may be invalid"),
}


def format_uptime(seconds):
    """將秒數格式化為人類可讀的運行時間。"""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def diagnose_error(e):
    """解析 CHRLINE 例外，回傳結構化的診斷資訊。

    Returns:
        dict with keys:
            code     - LINE error code (int) or "N/A"
            message  - raw error message string
            category - classified error type (e.g. SESSION_LOGGED_OUT, NETWORK_TIMEOUT)
            reason   - human-readable explanation
            is_token_issue - True if this error is related to token/session
    """
    err_str = str(e)

    result = {
        "code": "N/A",
        "message": err_str,
        "category": "UNKNOWN",
        "reason": "Cannot auto-diagnose",
        "is_token_issue": False,
    }

    # Parse CHRLINE error format: "Code: 8, Message: V3_TOKEN_CLIENT_LOGGED_OUT"
    if "Code:" in err_str and "Message:" in err_str:
        try:
            code_part = err_str.split("Code:")[1].split(",")[0].strip()
            msg_part = err_str.split("Message:")[1].strip()
            code = int(code_part)
            result["code"] = code
            result["message"] = msg_part
            if code in ERROR_REASONS:
                result["category"], result["reason"] = ERROR_REASONS[code]
            if code in [8, 20, 1000]:
                result["is_token_issue"] = True
        except (ValueError, IndexError):
            pass

    # Keyword-based fallback classification
    if "LOGGED_OUT" in err_str:
        result["is_token_issue"] = True
        result["category"] = "SESSION_LOGGED_OUT"
        result["reason"] = "LINE server force-terminated session (idle timeout / another device login / security policy)"
    elif "EXPIRED" in err_str:
        result["is_token_issue"] = True
        result["category"] = "TOKEN_EXPIRED"
        result["reason"] = "Access Token past its expiry"
    elif "AUTHENTICATION" in err_str or "auth" in err_str.lower():
        result["is_token_issue"] = True
        result["category"] = "AUTH_FAILED"
    elif "timeout" in err_str.lower() or "timed out" in err_str.lower():
        result["category"] = "NETWORK_TIMEOUT"
        result["reason"] = "Connection to LINE server timed out"
    elif "connect" in err_str.lower() or "socket" in err_str.lower():
        result["category"] = "NETWORK_ERROR"
        result["reason"] = "Cannot reach LINE server, check network"

    return result
