import os
import sys
import io
import time
import config
from CHRLINE import CHRLINE
import auth
import actions
from dashboard import safe_get

# 強制將 stdout 編碼設定為 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_sweep(cl, stage_name):
    print(f"\n==================================================")
    print(f"🚀 {stage_name}")
    print(f"==================================================")
    
    for i in range(1, 4):
        print(f"\n▶️ [第 {i} 次掃描]")
        try:
            # 1. 測試最基礎的 API (取得群組列表)
            chat_res = cl.getAllChatMids()
            gids = safe_get(chat_res, 'memberChatMids', 1) or chat_res
            if not isinstance(gids, list): 
                gids = list(gids) if gids else []
            print(f"  ✅ getAllChatMids() 呼叫成功！抓到 {len(gids)} 個群組")
            
            # 2. 測試進階 API (取得群組詳細資料)
            if gids:
                # 為了避免洗版，只拿前 3 個群組來測
                test_gids = gids[:3]
                chats_res = cl.getChats(test_gids, withMembers=True)
                chats = safe_get(chats_res, 'chats', 1) or chats_res
                if not isinstance(chats, list): 
                    chats = list(chats) if chats else []
                print(f"  ✅ getChats() 呼叫成功！成功取得 {len(chats)} 個群組的詳細資訊")
                
            # 3. 實際執行你的 active_sweep 邏輯
            print("  ➡️ 正在呼叫 actions.active_sweep(cl)...")
            actions.active_sweep(cl)
            print("  ✅ actions.active_sweep(cl) 執行完畢，無發生錯誤")
            
        except Exception as e:
            print(f"  ❌ 掃描過程發生錯誤: {e}")
            
        time.sleep(1) # 稍微休息一下避免被踢

def run_test():
    if not os.path.exists(config.TOKEN_FILE):
        print("❌ 找不到 Token 檔案")
        return

    with open(config.TOKEN_FILE, "r") as f:
        access_token = f.read().strip()
        
    print(f"🔑 [登入] 載入現有 Access Token: {access_token[:20]}...")
    
    try:
        cl = CHRLINE(
            access_token,
            device="DESKTOPMAC",
            version="8.4.1.3286",
            os_name="MAC",
            os_version="12.0"
        )
        print("✅ 登入成功！")
    except Exception as e:
        print(f"⚠️ 舊 Token 已失效 ({e})，正在呼叫 auth.try_startup_refresh()...")
        new_token = auth.try_startup_refresh()
        if not new_token:
            print("❌ 無法透過 Refresh Token 續命，請重新掃碼！")
            return
        print(f"✅ 成功救回！新的 Access Token: {new_token[:20]}...")
        cl = CHRLINE(
            new_token,
            device="DESKTOPMAC",
            version="8.4.1.3286",
            os_name="MAC",
            os_version="12.0"
        )
        print("✅ 使用新 Token 登入成功！")
    
    # 第一步：測試現有的 access token (3 times)
    test_sweep(cl, "第一階段 - 測試現有 Access Token")
    
    # 第二步：Refresh access token
    print("\n==================================================")
    print("🔄 準備進行 Refresh Access Token...")
    print("==================================================")
    
    # 這裡我們直接呼叫 auth.py 裡面的函式
    success = auth.try_refresh_token(cl)
    
    if not success:
        print("❌ Refresh 失敗！請檢查 log。")
        return
        
    print(f"🎉 Refresh 成功！目前記憶體內的 Token 已更新為: {cl.authToken[:20]}...")
    
    # 第三步：重複第一步 (3 times)
    test_sweep(cl, "第二階段 - 測試新的 Access Token")
    
    print("\n🎉 測試圓滿結束，新舊 Token 都能完美運作！")

if __name__ == "__main__":
    run_test()
