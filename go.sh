#!/bin/bash

cd ~/good_line_bot

# 啟動虛擬環境
source ~/line-env/bin/activate

# 檢查機器人是否已經在跑
if pgrep -f "python.*bot.py" > /dev/null; then
    echo "⚠️  機器人已經在背景執行中了！"
    echo "👉 請輸入 ./see.sh 即時觀看戰情看板"
    echo "👉 或輸入 ./stop.sh 停止機器人"
else
    # 用 nohup 在背景執行，Python 內部會自動將 print 攔截並寫入 logs/console.log (並自動按日輪轉)
    mkdir -p logs
    nohup python3 bot.py > /dev/null 2>&1 &
    echo $! > .bot.pid
    echo "✅ 機器人已成功在背景啟動！(PID: $(cat .bot.pid))"
    echo "👉 輸入 ./see.sh 即時觀看戰情看板"
    echo "👉 輸入 ./stop.sh 停止機器人"
fi
