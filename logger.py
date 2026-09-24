# logger.py
import logging
from logging.handlers import TimedRotatingFileHandler
import os

# ============================================================
# Log 目錄結構：按類別分資料夾
# logs/system/system_2026-09-23.log
# logs/error/error_2026-09-23.log
# logs/action/action_2026-09-23.log
# ============================================================

LOG_BASE = "logs"
LOG_DIRS = {
    "system": os.path.join(LOG_BASE, "system"),
    "error":  os.path.join(LOG_BASE, "error"),
    "action": os.path.join(LOG_BASE, "action"),
}

for d in LOG_DIRS.values():
    os.makedirs(d, exist_ok=True)


# ============================================================
# TagFilter：自動注入 [SYS]/[ERR]/[ACT] 標籤和 Emoji 前綴
# ============================================================

class TagFilter(logging.Filter):
    """根據 Logger 名稱與等級，自動注入標籤和 Emoji。"""

    TAG_MAP = {
        "System": "SYS",
        "Error":  "ERR",
        "Action": "ACT",
    }

    EMOJI_MAP = {
        logging.DEBUG:    "🔍",
        logging.INFO:     "ℹ️ ",
        logging.WARNING:  "⚠️",
        logging.ERROR:    "❌",
        logging.CRITICAL: "🔥",
    }

    def filter(self, record):
        record.tag = f"[{self.TAG_MAP.get(record.name, 'LOG')}]"
        record.emoji = self.EMOJI_MAP.get(record.levelno, "")
        return True


# ============================================================
# Formatter & Console Handler
# ============================================================

formatter = logging.Formatter(
    fmt="[%(asctime)s] %(tag)s %(emoji)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
console_handler.addFilter(TagFilter())


# ============================================================
# Logger 工廠
# ============================================================

def create_logger(name, category, level, retention_days):
    """建立帶有分類資料夾與日期輪轉的 Logger。

    Args:
        name: Logger 名稱 (System / Error / Action)
        category: 資料夾與檔名前綴 (system / error / action)
        level: 最低記錄等級
        retention_days: 保留天數
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        log_dir = LOG_DIRS[category]
        file_path = os.path.join(log_dir, f"{category}")

        # 每天午夜輪轉，檔名格式: system_2026-09-23.log
        file_handler = TimedRotatingFileHandler(
            filename=file_path + ".log",
            when="midnight",
            interval=1,
            backupCount=retention_days,
            encoding="utf-8",
        )
        file_handler.suffix = "_%Y-%m-%d.log"
        file_handler.namer = lambda name: name.replace(".log_", "_").replace(".log", "")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(TagFilter())

        logger.addFilter(TagFilter())
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# ============================================================
# 建立三個 Logger
# ============================================================

# 1. 系統日常 (保留 7 天)
sys_log = create_logger("System", "system", logging.INFO, 7)

# 2. 錯誤 (保留 30 天，WARNING 以上)
error_log = create_logger("Error", "error", logging.WARNING, 30)

# 3. 行動紀錄 (保留 30 天)
action_log = create_logger("Action", "action", logging.INFO, 30)


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


# ============================================================
# Console.log 自動輪轉器 (取代 bash nohup > console.log)
# ============================================================

class ConsoleRotator:
    """攔截 print() 輸出，並寫入會自動換日的 console.log 中。"""
    def __init__(self, filename):
        import sys
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # 設定會自動換日的 Handler (每天半夜輪轉)
        self.handler = TimedRotatingFileHandler(
            filename=filename,
            when="midnight",
            interval=1,
            backupCount=7,  # 保留 7 天的戰情看板與原始輸出
            encoding="utf-8"
        )
        self.handler.suffix = "_%Y-%m-%d"
        # 不加 formatter，保留最原始的排版
        
    def write(self, message):
        # 如果是空字串就不處理
        if not message:
            return
            
        # 寫入日誌檔 (觸發內建的換日邏輯)
        if self.handler.stream is None:
            self.handler.stream = self.handler._open()
            
        # 模擬 emit 的邏輯來檢查是否需要換日 (簡易實作)
        if self.handler.shouldRollover(logging.LogRecord("", 0, "", 0, message, None, None)):
            self.handler.doRollover()
            
        self.handler.stream.write(message)
        self.handler.stream.flush()
        
        # 同時輸出到原本的 stdout (確保終端機看得到)
        self.original_stdout.write(message)
        self.original_stdout.flush()

    def flush(self):
        if self.handler.stream:
            self.handler.stream.flush()
        self.original_stdout.flush()

def setup_console_rotator():
    import sys
    log_file = os.path.join(LOG_BASE, "console.log")
    rotator = ConsoleRotator(log_file)
    sys.stdout = rotator
    sys.stderr = rotator
    return rotator
