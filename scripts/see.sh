#!/bin/bash

# ===================================================================
# 專業級戰情監控看板 (Professional Monitoring TUI)
# ===================================================================

cd ~/good_line_bot

DASHBOARD_FILE="logs/dashboard.txt"
SYS_LOG_DIR="logs/system"
ACTION_LOG_DIR="logs/action"

while true; do
    clear
    
    # 1. 顯示靜態戰情看板 (Dashboard)
    if [ -f "$DASHBOARD_FILE" ]; then
        cat "$DASHBOARD_FILE"
    else
        echo -e "\n\n  📡 正在等待系統生成戰情看板...\n"
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🚨 最新攔截事件 (Action Logs) - 最近 5 筆"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 最新攔截事件
    ACTION_FILE="$ACTION_LOG_DIR/action.log"
    if [ -f "$ACTION_FILE" ]; then
        tail -n 5 "$ACTION_FILE" | while read -r line; do echo "    $line"; done
    else
        echo "    (尚無任何攔截事件紀錄)"
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ⚙️ 最新系統動態 (System Logs) - 最近 5 筆"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 最新系統動態
    SYS_FILE="$SYS_LOG_DIR/system.log"
    if [ -f "$SYS_FILE" ]; then
        tail -n 5 "$SYS_FILE" | while read -r line; do echo "    $line"; done
    else
        echo "    (尚無任何系統動態紀錄)"
    fi
    
    echo ""
    echo "💡 提示：按 [Ctrl+C] 離開觀看畫面，機器人仍會繼續在背景執行。"
    
    # 每秒刷新一次
    sleep 1
done
