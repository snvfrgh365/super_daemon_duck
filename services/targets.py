import os
from core.config import BASE_DIR

NAMES_FILE = os.path.join(BASE_DIR, "data", "target_names.txt")
UIDS_FILE = os.path.join(BASE_DIR, "data", "target_uids.txt")

_cache = {
    "names": set(),
    "uids": set(),
    "names_mtime": 0,
    "uids_mtime": 0
}

def _get_cached_lines(filepath, cache_key, mtime_key):
    """讀取並快取檔案內容，只有檔案修改時才重新讀取"""
    if not os.path.exists(filepath):
        return set()
    try:
        current_mtime = os.path.getmtime(filepath)
        if current_mtime > _cache[mtime_key]:
            with open(filepath, "r", encoding="utf-8") as f:
                # 僅移除換行符號，保留使用者刻意輸入的頭尾空白或特殊字元
                _cache[cache_key] = {line.rstrip("\r\n") for line in f if line.rstrip("\r\n")}
            _cache[mtime_key] = current_mtime
        return _cache[cache_key]
    except Exception as e:
        print(f"無法讀取目標設定檔 {filepath}: {e}")
        return _cache[cache_key]

def get_target_names():
    return _get_cached_lines(NAMES_FILE, "names", "names_mtime")

def get_target_uids():
    return _get_cached_lines(UIDS_FILE, "uids", "uids_mtime")

def is_target(name, mid):
    """判斷給定的名稱或 UID 是否在目標名單內 (要求絕對相等，非模糊比對)"""
    # 這裡不再對 name 使用 .strip()，確保連「空白」都絕對匹配
    if name and str(name) in get_target_names():
        return True
    if mid and str(mid).strip() in get_target_uids():
        return True
    return False

def init_target_files():
    """初始化預設的目標設定檔"""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(NAMES_FILE):
        with open(NAMES_FILE, "w", encoding="utf-8") as f:
            f.write("張興華\n")
    if not os.path.exists(UIDS_FILE):
        with open(UIDS_FILE, "w", encoding="utf-8") as f:
            f.write("")
