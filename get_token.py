import logging
logging.basicConfig(level=logging.INFO)
from CHRLINE import CHRLINE

# 準備三種目前最常被用來繞過 403 的官方版本號組合
devices_to_test = [
    {"device": "DESKTOPMAC", "version": "8.4.1.3286", "os_name": "MAC", "os_version": "12.0"},
    {"device": "IOSIPAD", "version": "13.4.0", "os_name": "iOS", "os_version": "16.0.0"},
    {"device": "DESKTOPMAC", "version": "8.3.0.3150", "os_name": "MAC", "os_version": "11.6"},
    {"device": "DESKTOPWIN", "version": "8.4.1.3286", "os_name": "Windows", "os_version": "10.0.0-NT-x64"},
    {"device": "CHROMEOS", "version": "3.1.2", "os_name": "ChromeOS", "os_version": "120.0"}
]

print("啟動自動協定切換測試...")

success = False
for d in devices_to_test:
    print(f"\n🔄 嘗試偽裝成 {d['device']} (版本: {d['version']}) 進行連線...")
    try:
        # 只帶入 CHRLINE 官方支援的 4 個參數
        cl = CHRLINE(
            device=d["device"],
            version=d["version"],
            os_name=d["os_name"],
            os_version=d["os_version"]
        )
        print("\n🎉 突破成功！請用手機掃描上方條碼/網址。")
        print("👉 你的專屬 Access Token 是：")
        print(cl.authToken)
        
        # 嘗試取得 Refresh Token
        r_token = getattr(cl, 'refreshToken', None)
        if r_token:
            print("\n👉 你的專屬 Refresh Token 是：")
            print(r_token)
            
        print("\n✅ 正在自動將 Token 儲存至檔案...")
        import os
        from core import config
        os.makedirs(os.path.dirname(config.TOKEN_FILE) or ".", exist_ok=True)
        
        with open(config.TOKEN_FILE, "w") as f:
            f.write(cl.authToken)
            
        if r_token:
            with open(config.REFRESH_TOKEN_FILE, "w") as f:
                f.write(r_token)
            print(f"✅ 已成功寫入 {config.TOKEN_FILE} 與 {config.REFRESH_TOKEN_FILE}")
        else:
            print(f"✅ 已成功寫入 {config.TOKEN_FILE} (本次登入未取得 Refresh Token，可能需要手動貼上)")
            
        success = True
        break  # 成功就跳出迴圈
        
    except Exception as e:
        print(f"❌ 被阻擋或發生錯誤: {e}")

if not success:
    print("\n⚠️ 測試完畢。如果全部都顯示 403，代表 LINE 官方已在伺服器端全面封鎖了目前 CHRLINE 的特徵。")
    print("這時只能等待原作者 (DeachSword) 在 GitHub 釋出繞過新版防護的更新了。")
    print("👉 建議：可以嘗試使用 Windows 11 本地 WSL，或者 Google Colab 雲端虛擬機來執行此腳本 (MAC 模式成功率較高)。")
