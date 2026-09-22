# dashboard.py
import time
import unicodedata
from datetime import datetime
import config


def safe_get(obj, attr, key):
    """安全取值器：同時支援 Object 屬性與 Dict 鍵值"""
    if hasattr(obj, attr):
        val = getattr(obj, attr)
        if val is not None:
            return val
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        if str(key) in obj:
            return obj[str(key)]
    return None


def extract_all_user_mids(obj):
    """暴力搜索器：無差別遞迴掃描封包內所有隱藏的 LINE 使用者 MID"""
    found = set()
    if isinstance(obj, str):
        # LINE 的個人 MID 永遠是 33 個字元且以 'u' 開頭
        if len(obj) == 33 and obj.startswith('u'):
            found.add(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            found.update(extract_all_user_mids(k))
            found.update(extract_all_user_mids(v))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            found.update(extract_all_user_mids(item))
    elif hasattr(obj, '__dict__'):
        found.update(extract_all_user_mids(obj.__dict__))
    return list(found)


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
    print(f"║  🛡️  Super Daemon Duck — 戰情看板{' ' * (W - 36)}║")
    print(f"╠{'═' * W}╣")
    print(f"║  🕒 時間:  {_pad(now_str, W - 12)}║")
    print(f"║  🤖 身分:  {_pad(bot_name, W - 12)}║")
    print(f"║  🆔 UID:   {_pad(bot_mid, W - 12)}║")
    print(f"║  ⏱️  運行:  {_pad(uptime_str, W - 13)}║")
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
    NAME_W = 18  # 名稱欄寬度
    UID_W = 33   # UID 欄寬度

    # 表頭
    print(f"     ┌{'─' * NUM_W}┬{'─' * NAME_W}┬{'─' * UID_W}┐")
    print(f"     │{_pad(' # ', NUM_W)}│{_pad(' 名稱', NAME_W)}│{_pad(' UID', UID_W)}│")
    print(f"     ├{'─' * NUM_W}┼{'─' * NAME_W}┼{'─' * UID_W}┤")

    for idx, (name, mid) in enumerate(members, 1):
        num_str = _pad(f" {idx:>2} ", NUM_W)
        name_str = _pad(f" {name}", NAME_W)
        mid_str = mid or "?"

        # 目標高亮
        if name == config.TARGET_NAME:
            uid_str = _pad(f" {mid_str}", UID_W)
            print(f"     │{num_str}│{name_str}│{uid_str}│ ← 🚨 目標！")
        else:
            uid_str = _pad(f" {mid_str}", UID_W)
            print(f"     │{num_str}│{name_str}│{uid_str}│")

    # 表尾
    print(f"     └{'─' * NUM_W}┴{'─' * NAME_W}┴{'─' * UID_W}┘")


# ============================================================
# 主報告
# ============================================================

def print_status_report(cl, boot_time=None):
    """印出完整的戰情看板。"""
    _print_header(cl, boot_time)

    try:
        # 1. 取得群組 IDs
        chat_res = cl.getAllChatMids()
        gids = safe_get(chat_res, 'memberChatMids', 1) or chat_res
        if not isinstance(gids, list):
            gids = list(gids)

        if not gids:
            print("\n⚠️  目前機器人尚未加入任何群組！")
        else:
            print(f"\n📊 防守中群組：{len(gids)} 個")
            print("━" * 64)

            # 2. 批次取得群組資料
            try:
                chats_res = cl.getChats(gids, withMembers=True)
            except Exception:
                chats_res = cl.getChats(gids)

            chats = safe_get(chats_res, 'chats', 1) or chats_res
            if not isinstance(chats, list):
                chats = list(chats)

            for i, chat in enumerate(chats, 1):
                try:
                    g_name = safe_get(chat, 'chatName', 6) or "未命名群組"

                    # 解析成員 MID
                    mids = []
                    extra = safe_get(chat, 'extra', 5)
                    group_extra = safe_get(extra, 'groupExtra', 1) if extra else None
                    member_mids = safe_get(group_extra, 'memberMids', 1) if group_extra else None

                    if isinstance(member_mids, dict):
                        mids = list(member_mids.keys())
                    elif isinstance(member_mids, list):
                        mids = member_mids

                    # Fallback: 暴力搜索法
                    if not mids:
                        mids = extract_all_user_mids(chat)

                    # 取得真名 + MID 配對
                    members = []
                    if mids:
                        contacts_res = cl.getContacts(mids)
                        contacts = safe_get(contacts_res, 'contacts', 1) or contacts_res
                        if not isinstance(contacts, list):
                            contacts = list(contacts)

                        for c in contacts:
                            name = safe_get(c, 'displayName', 22) or "未知"
                            mid = safe_get(c, 'mid', 1) or safe_get(c, 'contactMid', 1) or "?"
                            members.append((name, str(mid)))

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