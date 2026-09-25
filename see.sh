#!/bin/bash

# ===================================================================
# 專業級戰情監控看板 (Professional Monitoring TUI)
# ===================================================================
# 這個腳本會清空畫面並每秒刷新，顯示靜態的戰情看板與動態的 Log。
# 按 Ctrl+C 離開觀看，完全不影響背景運作的機器人。
# ===================================================================

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
    
    # 找出最新的 action log 檔案
    LATEST_ACTION=$(ls -t $ACTION_LOG_DIR/action_*.log 2>/dev/null | head -n 1)
    if [ -n "$LATEST_ACTION" ]; then
        tail -n 5 "$LATEST_ACTION" | while read -r line; do echo "    $line"; done
    else
        echo "    (尚無任何攔截事件紀錄)"
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ⚙️ 最新系統動態 (System Logs) - 最近 5 筆"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 找出最新的 system log 檔案
    LATEST_SYS=$(ls -t $SYS_LOG_DIR/system_*.log 2>/dev/null | head -n 1)
    if [ -n "$LATEST_SYS" ]; then
        tail -n 5 "$LATEST_SYS" | while read -r line; do echo "    $line"; done
    else
        echo "    (尚無任何系統動態紀錄)"
    fi
    
    echo ""
    echo "💡 提示：按 [Ctrl+C] 離開觀看畫面，機器人仍會繼續在背景執行。"
    
    # 每秒刷新一次
    sleep 1
done
