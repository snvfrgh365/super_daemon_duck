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
        # LINE 的 MID 通常長度為 33，且以 u, c, r 開頭 (u=User, c=Channel, r=Room)
        if len(obj) == 33 and obj[0] in ('u', 'c', 'r'):
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
