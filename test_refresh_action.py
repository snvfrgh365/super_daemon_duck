import os
import sys
import io
import time
import config
from CHRLINE import CHRLINE
import auth

# 強制將 stdout 編碼設定為 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def read_access():
    with open(config.TOKEN_FILE, "r") as f:
        return f.read().strip()

def run_test():
    print("="*50)
    print("🚀 嚴格基於 TXT 檔案的 Refresh Token 續命流程測試")
    print("="*50)

    # ==========================================
    # 步驟 1: 測試 txt 使否可以使用
    # ==========================================
    token_before = read_access()
    print(f"\n[步驟 1] 測試目前的 session_token.txt ({token_before[:15]}...)")
    try:
        cl_1 = CHRLINE(token_before, device="DESKTOPMAC", version="8.4.1.3286", os_name="MAC", os_version="12.0")
        profile1 = cl_1.getProfile()
        name1 = profile1.get(20) if isinstance(profile1, dict) else "未知"
        print(f"   ✅ 目前的 Token 完全有效！登入暱稱: 【{name1}】")
    except Exception as e:
        print(f"   ⚠️ 目前的 Token 測試失敗 (這很正常，因為可能已過期): {e}")

    # ==========================================
    # 步驟 2: 用 refresh 更新 access 的 txt
    # ==========================================
    print("\n[步驟 2] 強制執行 Refresh 並將新 Token 寫入 txt 檔案...")
    
    # 強制重置冷卻時間，確保一定會觸發 API (忽略 5 分鐘限制)
    auth.LAST_REFRESH_TIME = 0
    
    # 呼叫 auth.py 裡面的 try_startup_refresh，
    # 它的設計就是：無論原本 token 死活，都去拿一把新的，並呼叫 _save_new_tokens 寫入 txt
    new_token = auth.try_startup_refresh()
    
    if not new_token:
        print("   ❌ Refresh API 呼叫失敗！請檢查 Refresh Token 是否也過期了。")
        return
        
    print(f"   ✅ Refresh API 呼叫成功！")
    print(f"   ✅ 已經由 auth.py 自動覆寫 {config.TOKEN_FILE} 檔案！")

    # ==========================================
    # 步驟 3: use txt 的 new token 去 try
    # ==========================================
    token_after = read_access()
    print(f"\n[步驟 3] 重新讀取 txt 檔案，並測試新 Token ({token_after[:15]}...)")
    
    if token_before == token_after:
        print("   ❌ 嚴重錯誤：檔案裡的 Token 字串完全沒變！")
        return
    else:
        print("   ✅ 驗證成功：檔案內容已經確實變更。")
        
    try:
        # 完全依靠剛剛重新從檔案讀出來的 token_after 登入
        cl_3 = CHRLINE(token_after, device="DESKTOPMAC", version="8.4.1.3286", os_name="MAC", os_version="12.0")
        profile3 = cl_3.getProfile()
        name3 = profile3.get(20) if isinstance(profile3, dict) else "未知"
        print(f"   ✅ 新的 Token 完全有效！登入暱稱: 【{name3}】")
        
        print("\n==================================================")
        print("🎉 恭喜！整個「基於檔案的」Refresh 續命機制運作完美！")
        print("==================================================")
        
    except Exception as e:
        print(f"   ❌ 新 Token 測試失敗: {e}")

if __name__ == "__main__":
    run_test()
