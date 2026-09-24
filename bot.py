# bot.py
# retry
import os
import time
import random
from CHRLINE import CHRLINE
import config
import dashboard
import auth
import actions
from dashboard import safe_get
from logger import sys_log, error_log, action_log, diagnose_error, format_uptime, setup_console_rotator

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

    # [新增] 開機強制執行一次續命，確保獲得完整的 3 小時壽命
    sys_log.info("啟動【開機強制續命】機制，確保 Token 壽命重置...")
    auth.LAST_REFRESH_TIME = 0  # 忽略開機時可能的冷卻限制
    if auth.try_refresh_token(cl):
        sys_log.info("✅ 開機強制續命成功！")
    else:
        error_log.warning("⚠️ 開機強制續命失敗，將先使用原 Token 繼續執行。")

    # 開機初始化：立刻進行主動清場，再印出看板
    boot_time = time.time()
    actions.active_sweep(cl)
    dashboard.print_status_report(cl, boot_time)

    sys_log.info("防護系統已上線，主迴圈監聽中...")
    cl.revision = cl.getLastOpRevision()

    import threading

    def background_sweep():
        while True:
            start_time = time.time()
            
            try:
                actions.active_sweep(cl)
                dashboard.print_status_report(cl, boot_time)
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
                cl.revision = max(cl.revision, op[1] if isinstance(op, list) else safe_get(op, "revision", 1))
                op_type = op[3] if isinstance(op, list) else safe_get(op, "type", 3)

                # 攔截群組邀請 (Op 13, 124)
                if op_type in [13, 124]:
                    group_id = op[10] if isinstance(op, list) else safe_get(op, "param1", 10)
                    param3 = op[12] if isinstance(op, list) else safe_get(op, "param3", 12)
                    sep = "\x1e"
                    invited_mids = param3.split(sep) if isinstance(param3, str) else (param3 if isinstance(param3, list) else [param3])

                    for mid in invited_mids:
                        if not mid:
                            continue
                        contact = cl.getContact(str(mid))
                        if contact:
                            real_name = safe_get(contact, "displayName", 22)
                            action_log.info("[即時雷達] 偵測到邀請，被邀者: %s" % real_name)
                            if real_name == config.TARGET_NAME:
                                bot_mid = str(getattr(cl.profile, "mid", "")) if hasattr(cl, "profile") else ""
                                if str(mid) == bot_mid:
                                    continue
                                action_log.warning("[即時雷達] 警報！目標 [%s] 被邀請！" % config.TARGET_NAME)
                                actions.execute_ban(cl, group_id, mid, real_name, "cancel")

                # 發現入群 (Op 17, 130)
                elif op_type in [17, 130]:
                    group_id = op[10] if isinstance(op, list) else safe_get(op, "param1", 10)
                    joined_mid = op[11] if isinstance(op, list) else safe_get(op, "param2", 11)
                    
                    if not joined_mid:
                        continue
                        
                    contact = cl.getContact(str(joined_mid))

                    if contact:
                        real_name = safe_get(contact, "displayName", 22)
                        action_log.info("[即時雷達] 偵測到加入，入群者: %s" % real_name)
                        if real_name == config.TARGET_NAME:
                            bot_mid = str(getattr(cl.profile, "mid", "")) if hasattr(cl, "profile") else ""
                            if str(joined_mid) == bot_mid:
                                continue
                            action_log.warning("[即時雷達] 警報！目標 [%s] 闖入群組！" % config.TARGET_NAME)
                            actions.execute_ban(cl, group_id, joined_mid, real_name, "kick")

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
