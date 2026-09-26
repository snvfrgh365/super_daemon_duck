#!/bin/bash

# 停止背景執行的機器人

PID_FILE=~/good_line_bot/.bot.pid

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        echo "🛑 機器人已停止 (PID: $PID)"
    else
        rm -f "$PID_FILE"
        echo "⚠️  機器人已經不在執行了（PID 檔案已清除）"
    fi
else
    # Fallback: 用 pkill 搜尋
    if pgrep -f "python.*main.py" > /dev/null; then
        pkill -f "python.*main.py"
        echo "🛑 機器人已停止"
    else
        echo "⚠️  找不到執行中的機器人"
    fi
fi
