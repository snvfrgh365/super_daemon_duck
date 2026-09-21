# LINE 群組防護機器人 (Anti-Bot) 使用教學

本專案主要用於防止特定使用者（如：張興華）進入 LINE 群組。機器人會在背景 24 小時無間斷運行，並具備自動踢除與防護功能。

## 📍 系統需求
- Linux 環境 (已安裝 Python 3.8+ 及 `tmux`)
- 已經取得有效的 LINE Session Token (放置於 `tokens/session_token.txt`)

---

## 🛠️ 第一步：環境建置 (首次安裝)

打開 Linux 終端機 (Terminal) 後，請依序執行以下指令：

### 1. 確保腳本具備執行權限
確保你的 `go.sh` 與 `see.sh` 可以被系統執行：
```bash
# 進入機器人專案資料夾 (請依照你實際的路徑修改，腳本預設是 ~/good_line_bot)
cd ~/good_line_bot

# 賦予腳本執行權限
chmod +x go.sh see.sh
```

### 2. 建立 Python 虛擬環境 (Virtual Environment)
根據腳本設定，虛擬環境預設建立在 `~/line-env`：
```bash
python3 -m venv ~/line-env
```

### 3. 啟動虛擬環境並安裝相依套件
```bash
# 啟動虛擬環境
source ~/line-env/bin/activate

# 安裝所需套件 (包含核心模組 CHRLINE)
pip install -r requirements.txt
```

---

## 🔑 第二步：取得 LINE Token

機器人需要透過 Token 才能操作你的 LINE 帳號。如果你尚未取得 Token，或是遇到 403 被阻擋的問題，請使用專案內附的腳本來獲取。

> **💡 建議執行環境：**
> 如果你在本機執行一直遇到 `403 Forbidden`，建議使用 **Windows 11 的本地 WSL** 或是 **Google Colab 雲端虛擬機** 進行測試，其中 **MAC 模式** 的成功率通常最高！

執行以下指令開始取得 Token：
```bash
python get_token.py
```
程式會自動嘗試不同的裝置特徵（Windows / MAC / ChromeOS）來繞過阻擋。成功後，會顯示 QR Code 網址，請用手機 LINE 掃描登入。

登入成功後，終端機會印出 `Access Token` 與 `Refresh Token`，請分別將它們存入 `tokens/` 資料夾內：
- `tokens/session_token.txt` (放入 Access Token)
- `tokens/refresh_token.txt` (放入 Refresh Token)

---

## 🚀 第三步：啟動與操作

### 啟動機器人 (背景執行)
只要執行 `go.sh`，系統就會透過 `tmux` 在背景開啟機器人：
```bash
./go.sh
```
> **提示：** 啟動後，即使你關閉終端機或登出 SSH，機器人依舊會持續運作！

### 觀看戰情看板 (監控畫面)
想要查看機器人目前的狀態或是抓到了誰，請執行：
```bash
./see.sh
```
> ⚠️ **重要操作注意：**
> 進入戰情看板後，**絕對不要按 `Ctrl + C`**（這會直接強制關閉機器人）。
> 要退出監控畫面並讓機器人繼續在背景跑，請按鍵盤上的：
> **`Ctrl + B`** (按完放開)，然後再按 **`D`** (Detach)。

### 如何關閉 / 停止機器人
如果活動結束，想要徹底關閉機器人，請使用 `tmux` 指令強制砍掉進程：
```bash
tmux kill-session -t linebot
```
執行後沒有跳出錯誤訊息就代表已經成功關閉了。
