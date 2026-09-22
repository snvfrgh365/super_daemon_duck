#!/bin/bash

# 即時觀看戰情看板（用 tail -f 追蹤最新輸出）
# 按 Ctrl+C 離開觀看，機器人不會停止

LOG=~/good_line_bot/logs/console.log

if [ ! -f "$LOG" ]; then
    echo "❌ 找不到 log 檔案，請先執行 ./go.sh 啟動機器人！"
    exit 1
fi

echo "🔗 正在連線至戰情看板..."
echo "💡 提示：按 Ctrl+C 即可離開觀看，機器人會繼續在背景執行。"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sleep 1
tail -f "$LOG"
