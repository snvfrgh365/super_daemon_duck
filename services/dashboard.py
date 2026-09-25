# dashboard.py
import time
import unicodedata
from datetime import datetime
from core import config
import sys
import io
import os


from utils.helpers import safe_get, extract_all_user_mids


# ============================================================
# 排版工具
# ============================================================

def _display_width(text):
    """計算字串在終端機中的顯示寬度（全形字佔 2 格）。"""
    width = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width


def _pad(text, target_width):
    """將字串用空格補齊到指定的顯示寬度（考慮全形字元）。"""
    current = _display_width(text)
    return text + " " * max(0, target_width - current)


def _truncate(text, max_width):
    """將字串截斷到指定的顯示寬度以內，若截斷則補上 '...'"""
    if _display_width(text) <= max_width:
        return text
    result = ""
    current_width = 0
    for ch in text:
        w = 2 if unicodedata.east_asian_width(ch) in ('F', 'W') else 1
        if current_width + w > max_width - 3:
            break
        result += ch
        current_width += w
    return result + "..."


# ============================================================
# 表頭
# ============================================================

def _print_header(cl, boot_time):
    """印出帶有 Box Drawing 邊框的表頭。"""
    W = 64  # 內容寬度

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bot_name = safe_get(cl.profile, "displayName", 20) or "Unknown"
    bot_mid = safe_get(cl.profile, "mid", 1) or "Unknown"

    # 運行時間
    if boot_time:
        uptime = time.time() - boot_time
        hours, rem = divmod(int(uptime), 3600)
        mins, secs = divmod(rem, 60)
        uptime_str = f"{hours}h {mins}m {secs}s"
    else:
        uptime_str = "N/A"

    print()
    print(f"╔{'═' * W}╗")
    print(f"║  🛡️  SUPER DAEMON DUCK — 戰場監控系統{' ' * (W - 39)}║")
    print(f"╠{'═' * W}╣")
    print(f"║  [系統狀態]{' ' * (W - 12)}║")
    print(f"║  🕒 時間:  {_pad(now_str, W - 12)}║")
    print(f"║  🤖 身分:  {_pad(bot_name, W - 12)}║")
    print(f"║  🆔 UID:   {_pad(bot_mid, W - 12)}║")
    
    from core import auth
    refresh_info = f"{uptime_str} (成功續命: {auth.REFRESH_SUCCESS_COUNT} 次)"
    print(f"║  ⏱️  運行:  {_pad(refresh_info, W - 13)}║")
    print(f"╠{'═' * W}╣")
    
    from services import targets
    names = list(targets.get_target_names())
    uids = list(targets.get_target_uids())
    
    tracking_title = f"[追蹤名單] (名稱: {len(names)}, UID: {len(uids)})"
    print(f"║  {_pad(tracking_title, W - 2)}║")
    
    names_str = ", ".join(names) if names else "無"
    uids_str = ", ".join(uids) if uids else "無"
    
    print(f"║  📛 名稱: {_pad(_truncate(names_str, W - 12), W - 12)}║")
    print(f"║  🔑 UID:  {_pad(_truncate(uids_str, W - 12), W - 12)}║")
    print(f"╚{'═' * W}╝")


# ============================================================
# 成員表格
# ============================================================

def _print_member_table(members):
    """印出成員表格（每人一行，含序號、名稱、UID、目標標記）。

    Args:
        members: list of (name, mid) tuples
    """
    NUM_W = 4    # 序號欄寬度
    NAME_W = 60  # 名稱欄寬度 (加長以容納曾用名與時間戳)

    # 表頭
    print(f"     ┌{'─' * NUM_W}┬{'─' * NAME_W}┐")
    print(f"     │{_pad(' # ', NUM_W)}│{_pad(' 名稱 (曾用名與日期)', NAME_W)}│")
    print(f"     ├{'─' * NUM_W}┼{'─' * NAME_W}┤")

    for idx, (name, history, mid) in enumerate(members, 1):
        num_str = _pad(f" {idx:>2} ", NUM_W)
        
        # 組合顯示名稱與歷史紀錄
        display_name = name
        if len(history) > 1:
            past_records = []
            
            # 為了避免過長，最多只顯示最近 2 個曾用名
            history_to_show = history[:-1]
            hidden_count = 0
            
            if len(history_to_show) > 2:
                hidden_count = len(history_to_show) - 2
                history_to_show = history_to_show[-2:]
                
            for record in history_to_show:
                if isinstance(record, dict) and 'name' in record:
                    short_date = record.get('seen_at', '')[5:10] # '09-24'
                    past_records.append(f"{record['name']}({short_date})")
                else:
                    past_records.append(str(record))
            
            past_names = " -> ".join(past_records)
            if hidden_count > 0:
                past_names = f"...等{hidden_count}個 -> " + past_names
                
            display_name = f"{name} (曾用: {past_names})"
            
        # 聰明截斷：如果超出寬度，強行截斷避免排版跑掉，並確保括號完美收尾
        display_width = _display_width(display_name)
        if display_width > NAME_W - 2:
            suffix = "...)" if len(history) > 1 else "..."
            
            # 逐字刪減直到加上 suffix 後符合寬度
            while _display_width(display_name) + _display_width(suffix) > NAME_W - 2:
                display_name = display_name[:-1]
                
            display_name += suffix
            
        name_str = _pad(f" {display_name}", NAME_W)

        # 目標高亮 (保留內部使用 mid 來高亮的邏輯，但不再印出 mid)
        from services import targets
        if targets.is_target(name, mid):
            print(f"     │{num_str}│{name_str}│ ← 🚨 目標！")
        else:
            print(f"     │{num_str}│{name_str}│")

    # 表尾
    print(f"     └{'─' * NUM_W}┴{'─' * NAME_W}┘")


# ============================================================
# 主報告
# ============================================================

def print_status_report(cl, boot_time=None, state=None):
    """印出完整的戰情看板，並導向至 logs/dashboard.txt"""
    if state is None:
        state = []
        
    os.makedirs('logs', exist_ok=True)
    
    original_stdout = sys.stdout
    buffer = io.StringIO()
    sys.stdout = buffer
    
    try:
        _print_header(cl, boot_time)

        if not state:
            print("\n⚠️  目前機器人尚未加入任何群組！")
        else:
            print(f"\n📊 防守中群組：{len(state)} 個")
            print("━" * 64)

            for i, group in enumerate(state, 1):
                try:
                    g_name = group.get("group_name", "未命名群組")
                    members_data = group.get("members", [])
                    invitees_data = group.get("invitees", [])
                    
                    # 先建立 members_dict，包含 member 與 invitee
                    members_dict = {}
                    for u in members_data + invitees_data:
                        members_dict[u["mid"]] = u["name"]

                    # 更新並載入 UID 歷史資料庫
                    from services.uid_db import update_uid_db
                    db = update_uid_db(members_dict)

                    # 轉為 (name, history, mid) 格式
                    members = []
                    for mid, current_name in members_dict.items():
                        history = db.get(str(mid), [{"name": current_name}])
                        members.append((current_name, history, str(mid)))

                    print(f"\n  {i}. 🏷️  {g_name}（{len(members)} 人）")

                    if members:
                        _print_member_table(members)
                    else:
                        print("     [!] 偵錯警告：此群組底層完全抓不到 MID。")

                except Exception as e:
                    print(f"\n  {i}. [群組資料讀取失敗] {e}")

    except Exception as e:
        print(f"❌ 讀取群組列表發生例外: {e}")

    print("━" * 64 + "\n")
    
    # 恢復原本的 stdout，並將 buffer 寫入檔案
    sys.stdout = original_stdout
    
    from core.config import BASE_DIR
    dashboard_file = os.path.join(BASE_DIR, "logs", "dashboard.txt")
    with open(dashboard_file, "w", encoding="utf-8") as f:
        f.write(buffer.getvalue())