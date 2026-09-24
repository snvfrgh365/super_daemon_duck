import json
import os

DB_PATH = "data/uid_history.json"

def update_uid_db(members_dict):
    """
    更新 UID 與名稱的對應資料庫，並記錄名稱變更歷史。
    members_dict: dict, format { "uid1": "Current Name", "uid2": "Another Name" }
    回傳: dict, 最新完整的歷史紀錄 (e.g. { "uid1": ["Old Name", "Current Name"] })
    """
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    
    # 讀取現有資料庫
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                db = json.load(f)
        except Exception:
            db = {}
    else:
        db = {}
        
    changed = False
    
    for uid, name in members_dict.items():
        if not name or name == "官方帳號 / 未知":
            continue
            
        if uid not in db:
            db[uid] = [name]
            changed = True
        else:
            # 如果目前名字和紀錄中最後一個名字不同，代表改名了
            if db[uid][-1] != name:
                if name in db[uid]:
                    # 以前用過這個名字，把它移到最新
                    db[uid].remove(name)
                db[uid].append(name)
                changed = True
                
    if changed:
        try:
            with open(DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"寫入 UID 資料庫失敗: {e}")
            
    return db
