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
