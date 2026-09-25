import json
import os
from datetime import datetime

from core import config

DB_PATH = config.UID_DB_FILE
def _get_now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _migrate_db(db):
    """
    將舊版的純字串陣列遷移成帶有時間戳記的結構。
    Old: { "uid1": ["Name1", "Name2"] }
    New: { "uid1": [{"name": "Name1", "seen_at": "2026-09..."}] }
    """
    migrated = False
    for uid, history in db.items():
        if not history: continue
        if isinstance(history[0], str):
            # 舊版格式，進行轉換
            new_history = [{"name": n, "seen_at": _get_now_str()} for n in history]
            db[uid] = new_history
            migrated = True
    return migrated

def update_uid_db(members_dict):
    """
    更新 UID 與名稱的對應資料庫，並記錄名稱變更歷史（含時間戳記）。
    members_dict: dict, format { "uid1": "Current Name" }
    回傳: dict, 最新完整的歷史紀錄 (結構為 List[dict])
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
        
    changed = _migrate_db(db)
    
    for uid, name in members_dict.items():
        if not name or name == "官方帳號 / 未知":
            continue
            
        if uid not in db:
            db[uid] = [{"name": name, "seen_at": _get_now_str()}]
            changed = True
        else:
            # 檢查目前最後一個名字是否與新名字相同
            last_entry = db[uid][-1]
            if last_entry["name"] != name:
                # 檢查是否以前用過
                existing_idx = next((i for i, v in enumerate(db[uid]) if v["name"] == name), -1)
                
                if existing_idx != -1:
                    # 如果以前用過，更新它的時間並把它移到最後面（最新）
                    entry = db[uid].pop(existing_idx)
                    entry["seen_at"] = _get_now_str()
                    db[uid].append(entry)
                else:
                    # 第一次用這個名字
                    db[uid].append({"name": name, "seen_at": _get_now_str()})
                
                changed = True
                
    if changed:
        try:
            with open(DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"寫入 UID 資料庫失敗: {e}")
            
    return db
