#!/bin/bash

# 嘗試連接名為 linebot 的虛擬螢幕
if tmux has-session -t linebot 2>/dev/null; then
    echo "🔗 正在連線至戰情看板..."
    echo "💡 提示：觀看結束後，請按 [Ctrl + B] 放開後再按 [D] 回到此畫面，千萬不要按 Ctrl+C！"
    sleep 2
    tmux attach -t linebot
else
    echo "❌ 找不到執行中的機器人 (linebot)，請先執行 ./go.sh 啟動！"
fi
