# dashboard.py
from datetime import datetime

def safe_get(obj, attr, key):
    """安全取值器：同時支援 Object 屬性與 Dict 鍵值"""
    if hasattr(obj, attr):
        val = getattr(obj, attr)
        if val is not None: return val
    if isinstance(obj, dict):
        if key in obj: return obj[key]
        if str(key) in obj: return obj[str(key)]
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

def print_status_report(cl):
    print("\n" + "═" * 50)
    print(f"🕒 現在時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 機器人身分: {cl.profile[20]}")
    print("-" * 50)
    print("📊 [即時群組監控報告]")
    
    try:
        # 1. 取得群組 IDs
        chat_res = cl.getAllChatMids()
        gids = safe_get(chat_res, 'memberChatMids', 1) or chat_res
        if not isinstance(gids, list): gids = list(gids)

        if not gids:
            print("⚠️ 目前機器人尚未加入任何群組！")
        else:
            print(f"👉 總共防守 {len(gids)} 個群組：")
            
            # 2. 批次取得群組資料 (強制要求伺服器附帶成員名單)
            try:
                chats_res = cl.getChats(gids, withMembers=True)
            except Exception:
                chats_res = cl.getChats(gids)
                
            chats = safe_get(chats_res, 'chats', 1) or chats_res
            if not isinstance(chats, list): chats = list(chats)
                
            for i, chat in enumerate(chats, 1):
                try:
                    # 取得群組名稱
                    g_name = safe_get(chat, 'chatName', 6) or "未命名群組"
                    
                    # 第一階段：標準路徑解析
                    mids = []
                    extra = safe_get(chat, 'extra', 5)
                    group_extra = safe_get(extra, 'groupExtra', 1) if extra else None
                    member_mids = safe_get(group_extra, 'memberMids', 1) if group_extra else None
                    
                    if isinstance(member_mids, dict):
                        mids = list(member_mids.keys())
                    elif isinstance(member_mids, list):
                        mids = member_mids
                        
                    # 第二階段：如果標準路徑失敗 (0人)，啟動暴力搜索法
                    if not mids:
                        mids = extract_all_user_mids(chat)
                        
                    # 3. 取得真名
                    m_names = []
                    if mids:
                        contacts_res = cl.getContacts(mids)
                        contacts = safe_get(contacts_res, 'contacts', 1) or contacts_res
                        if not isinstance(contacts, list): contacts = list(contacts)
                        
                        for c in contacts:
                            name = safe_get(c, 'displayName', 22) or "未知"
                            m_names.append(name)
                            
                    print(f"\n  {i}. {g_name} (共 {len(m_names)} 人)")
                    print(f"     👥 成員: {', '.join(m_names)}")
                    
                    if len(m_names) == 0:
                        print(f"     [!] 偵錯警告：此群組底層完全抓不到 MID。")
                        
                except Exception as e:
                    print(f"\n  {i}. [群組資料讀取失敗] {e}")
    except Exception as e:
        print(f"❌ 讀取群組列表發生例外: {e}")
    
    print("═" * 50 + "\n")