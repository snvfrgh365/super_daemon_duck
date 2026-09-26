# bot.py
# retry
import os
import time
import random
from CHRLINE import CHRLINE
from core import config
from services import dashboard
from core import auth
from services import actions
from utils.helpers import safe_get
from core.line_constants import OpField
from services import handlers
from core.logger import sys_log, error_log, action_log, diagnose_error, format_uptime, setup_console_rotator

# 啟動 Console 自動輪轉機制
setup_console_rotator()

def print_boot_banner():
    banner = f"\n{'█'*64}\n{' '*18}🚀 BOT SYSTEM RESTART {' '*19}\n{'█'*64}\n"
    print(banner)
    sys_log.info(f"\n{'='*40}\n🚀 系統啟動標記 (SYSTEM START)\n{'='*40}")
    error_log.warning(f"\n{'='*40}\n🚀 系統啟動標記 (SYSTEM START)\n{'='*40}")
    action_log.info(f"\n{'='*40}\n🚀 系統啟動標記 (SYSTEM START)\n{'='*40}")

print_boot_banner()

CHRLINE_PARAMS = {
    "device": "DESKTOPMAC",
    "version": "8.4.1.3286",
    "os_name": "MAC",
    "os_version": "12.0",
}


def create_client(token):
    """Build CHRLINE client with specified token."""
    return CHRLINE(token, **CHRLINE_PARAMS)


def run_bot():
    from services import targets
    targets.init_target_files()
    
    if not os.path.exists(config.TOKEN_FILE):
        error_log.error("找不到 %s" % config.TOKEN_FILE)
        return

    with open(config.TOKEN_FILE, "r") as f:
        token = f.read().strip()

    sys_log.info("正在使用本機 Token 連線至 LINE 伺服器...")
    cl = None
    try:
        cl = create_client(token)
    except Exception as e:
        error_log.error("登入失敗: %s" % e)
        # ---- 啟動時 Token 已過期，嘗試用 Refresh Token 續命 ----
        new_token = auth.try_startup_refresh()
        if new_token:
            sys_log.info("使用新 Token 重新連線中...")
            try:
                cl = create_client(new_token)
            except Exception as e2:
                error_log.error("續命後仍然無法登入: %s" % e2)
                return
        else:
            error_log.error("無法自動續命，請手動重新掃碼取得 Token (python get_token.py)")
            return

    sys_log.info("✅ 登入成功！")
    
    # [新] 開機強制續命一次，確保有完整的 3 小時壽命
    sys_log.info("【開機強制續命】嘗試確保 Token 壽命重置...")
    auth.LAST_REFRESH_TIME = 0  # 忽略任何可能的冷卻限制
    if auth.try_refresh_token(cl):
        sys_log.info("✅ 開機強制續命成功。")
    else:
        error_log.warning("⚠️ 開機強制續命失敗，將使用舊 Token 繼續嘗試...")
    try:
        # 開機初始化：立刻進行主動清場，再印出看板
        boot_time = time.time()
        from services import scanner
        state = scanner.fetch_group_state(cl)
        actions.active_sweep(cl, state)
        dashboard.print_status_report(cl, boot_time, state)

        sys_log.info("防護系統已上線，主迴圈監聽中...")
        cl.revision = cl.getLastOpRevision()
    except Exception as e:
        import traceback
        error_log.error("啟動初始化崩潰: %s\n%s" % (e, traceback.format_exc()))
        sys_log.error("啟動初始化崩潰，機器人停止。")
        return

    import threading

    from services import scanner
    def background_sweep():
        while True:
            start_time = time.time()
            
            try:
                state = scanner.fetch_group_state(cl)
                actions.active_sweep(cl, state)
                dashboard.print_status_report(cl, boot_time, state)
            except Exception as e:
                error_log.error("背景巡邏發生異常: %s" % e)
                
            # 計算掃描與畫看板耗費了多少時間
            elapsed = time.time() - start_time
            
            # 目標休息時間
            target_sleep = random.uniform(config.REPORT_INTERVAL_MIN, config.REPORT_INTERVAL_MAX)
            
            # 把剛剛耗費的時間從休息時間中扣除 (如果耗時超過目標時間，就不休息直接進入下一輪)
            actual_sleep = max(0, target_sleep - elapsed)
            time.sleep(actual_sleep)

    # 啟動背景巡邏執行緒
    sweep_thread = threading.Thread(target=background_sweep, daemon=True)
    sweep_thread.start()

    def proactive_refresh():
        import datetime
        while True:
            # 隨機等待 2 到 2.5 小時 (避免精準 2.5 踩線被抓)
            refresh_interval = random.uniform(2 * 3600, 2.5 * 3600)
            next_time = datetime.datetime.now() + datetime.timedelta(seconds=refresh_interval)
            next_time_str = next_time.strftime('%Y-%m-%d %H:%M:%S')
            sys_log.info(f"⏳ [背景續命] 下次主動更新 Token 時間預計為: {next_time_str}")
            time.sleep(refresh_interval)
            
            try:
                sys_log.info("🔄 [背景續命] Access Token 已接近壽命極限，嘗試主動更換...")
                if auth.try_refresh_token(cl):
                    sys_log.info("✅ [背景續命] 成功更換 Access Token，延長生命週期！")
                    try:
                        cl.revision = cl.getLastOpRevision()
                    except:
                        pass
                else:
                    error_log.warning("⚠️ [背景續命] 嘗試更新 Token 失敗")
            except Exception as e:
                error_log.error(f"❌ [背景續命] 發生異常: {e}")

    # 啟動主動續命執行緒
    refresh_thread = threading.Thread(target=proactive_refresh, daemon=True)
    refresh_thread.start()


    error_streak = 0

    while True:
        try:
            # 即時事件監聽 (改用 sync 替代被拔除的 fetchOps)
            try:
                ops_res = cl.sync(cl.revision)
                ops = safe_get(ops_res, "operations", 1) or []
            except Exception as e:
                if "fetchOps" in str(e) or "sync" in str(e):
                    ops = []
                else:
                    raise e

            error_streak = 0  # 成功一次就重置

            for op in ops:
                cl.revision = max(cl.revision, op[OpField.REVISION] if isinstance(op, list) else safe_get(op, "revision", OpField.REVISION))
                handlers.handle_operation(cl, op)

        except Exception as e:
            error_streak += 1
            uptime_sec = time.time() - boot_time
            uptime_str = format_uptime(uptime_sec)
            diagnosis = diagnose_error(e)

            error_log.error(
                "[CRASH #%d] %s | reason: %s | code: %s | msg: %s | uptime: %s | exception: %s: %s"
                % (error_streak, diagnosis["category"], diagnosis["reason"],
                   diagnosis["code"], diagnosis["message"], uptime_str,
                   type(e).__name__, e)
            )

            if diagnosis["is_token_issue"]:
                error_log.error("[DIAG] Token issue detected, attempting refresh...")
                if auth.try_refresh_token(cl):
                    error_streak = 0
                    try:
                        cl.revision = cl.getLastOpRevision()
                    except Exception:
                        pass
                else:
                    error_log.error("[DIAG] Refresh failed, waiting 10s before retry")
                    time.sleep(10)
            else:
                wait = min(10 * error_streak, 60)
                error_log.warning("[DIAG] Non-token issue, retrying in %ds" % wait)
                time.sleep(wait)

        time.sleep(1)


if __name__ == "__main__":
    run_bot()
