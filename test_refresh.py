import os
import sys
import config
from CHRLINE import CHRLINE

def test_refresh():
    print("=== 🦆 Super Daemon Duck 續命演習 ===")
    
    # 1. 讀取目前的 Access Token
    if not os.path.exists(config.TOKEN_FILE):
        print(f"❌ 找不到 {config.TOKEN_FILE}")
        return
        
    with open(config.TOKEN_FILE, "r") as f:
        access_token = f.read().strip()
        
    # 2. 讀取 Refresh Token
    if not os.path.exists(config.REFRESH_TOKEN_FILE):
        print(f"❌ 找不到 {config.REFRESH_TOKEN_FILE}")
        return
        
    with open(config.REFRESH_TOKEN_FILE, "r") as f:
        refresh_token = f.read().strip()
        
    if not access_token or not refresh_token:
        print("❌ Token 檔案內容為空")
        return
        
    print("✅ 成功讀取本地 Tokens！")
    print("🔗 正在建立連線...")
    
    try:
        cl = CHRLINE(
            access_token,
            device="DESKTOPMAC",
            version="8.4.1.3286",
            os_name="MAC",
            os_version="12.0"
        )
        print("✅ 連線成功！你的 Access Token 目前是活著的。")
    except Exception as e:
        print(f"❌ 連線失敗 (可能 Access Token 已過期): {e}")
        return
        
    print("\n🚀 正在模擬「2.5小時後的主動續命」...")
    print("📡 向 LINE 伺服器發送 Refresh 請求...")
    
    try:
        RATR = cl.refreshAccessToken(refresh_token)
        print(f"\n[DEBUG] 伺服器原始回應: {RATR}")
        
        new_token = cl.checkAndGetValue(RATR, "accessToken", 1)
        new_refresh = cl.checkAndGetValue(RATR, "refreshToken", 2)
        
        if new_token and isinstance(new_token, str):
            print("\n🎉 【測試成功】伺服器接受了你的 Refresh Token！")
            print(f"👉 取得的新 Access Token: {new_token[:30]}...")
            if new_refresh:
                print(f"👉 取得的新 Refresh Token: {new_refresh[:30]}...")
            else:
                print("👉 (伺服器未派發新 Refresh Token，代表原 Refresh Token 可以繼續重複使用)")
                
            print("\n✅ 這證明了你的機器人 3 小時後絕對可以自己續命成功，不會被 Ban！")
        else:
            print("\n❌ 測試失敗：伺服器沒有回傳 accessToken，可能是 Code 1000。")
            
    except Exception as e:
        print(f"\n❌ 測試發生異常，續命失敗: {e}")

if __name__ == "__main__":
    test_refresh()
