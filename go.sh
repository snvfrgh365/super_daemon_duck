#!/bin/bash

# 進入機器人資料夾
cd ~/good_line_bot

# 啟動虛擬環境
source ~/line-env/bin/activate

# 檢查 linebot 是否已經在跑
if tmux has-session -t linebot 2>/dev/null; then
    echo "⚠️ 機器人已經在背景執行中了！"
    echo "👉 請輸入 ./see.sh 進入觀看戰情看板"
else
    # 在背景建立一個名為 linebot 的 tmux 視窗，並立刻執行 python bot.py
    tmux new-session -d -s linebot "python bot.py"
    echo "✅ 機器人已成功在背景啟動，開始 24 小時無間斷防護！"
    echo "👉 隨時輸入 ./see.sh 即可觀看戰情看板"
    echo " (觀看完畢請按 Ctrl + B，放開後再按 D 離開，不要按 Ctrl+C 哦！)"
fi
