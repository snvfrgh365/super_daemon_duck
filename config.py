# config.py

TARGET_NAME = "Super_Duck!"
TOKEN_FILE = "tokens/session_token.txt"
REFRESH_TOKEN_FILE = "tokens/refresh_token.txt"

# 系統防護設定
ACTION_COOLDOWN = 1.5  # 發現目標後 1.5 秒開始執行封鎖
API_DELAY = 1.0        # 封鎖後 1.0 秒執行踢出        

# 戰情看板更新頻率 (秒) - 加入隨機延遲避免被判定為機器人
REPORT_INTERVAL_MIN = 4.0
REPORT_INTERVAL_MAX = 6.5

# 主動續命頻率 (秒)
# 根據實測 log，LINE session 約 3 小時會 idle timeout
# 在 2 ~ 2.5 小時之間隨機 refresh，搶在 timeout 之前續命
PROACTIVE_REFRESH_MIN = 2 * 60 * 60       # 2 小時 (7200 秒)
PROACTIVE_REFRESH_MAX = 2.5 * 60 * 60     # 2.5 小時 (9000 秒)