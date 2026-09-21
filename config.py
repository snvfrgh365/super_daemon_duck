# config.py

TARGET_NAME = "張興華"
TOKEN_FILE = "tokens/session_token.txt"
REFRESH_TOKEN_FILE = "tokens/refresh_token.txt"

# 系統防護設定
ACTION_COOLDOWN = 1.5  # 發現目標後 1.5 秒開始執行封鎖
API_DELAY = 1.0        # 封鎖後 1.0 秒執行踢出        

# 戰情看板更新頻率 (秒) - 加入隨機延遲避免被判定為機器人
REPORT_INTERVAL_MIN = 4.0
REPORT_INTERVAL_MAX = 6.5