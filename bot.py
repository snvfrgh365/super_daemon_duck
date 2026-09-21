# bot.py
import os
import time
from CHRLINE import CHRLINE
import config
import dashboard
import auth
import actions
from dashboard import safe_get
from logger import sys_log, error_log, action_log

def run_bot():
    if not os.path.exists(config.TOKEN_FILE):
        error_log.error(f"❌ 找不到 {config.TOKEN_FILE}")
        return

    with open(config.TOKEN_FILE, "r") as f:
        token = f.read().strip()

    sys_log.info("🔗 正在使用本機 Token 連線至 LINE 伺服器...")
    try:
        cl = CHRLINE(
            token, 
            device="DESKTOPMAC",
            version="8.4.1.3286",
            os_name="MAC",
            os_version="12.0"
        )
    except Exception as e:
        error_log.error(f"❌ 登入失敗: {e}")
        return

    # 開機初始化：印出看板並立刻進行主動清場
    dashboard.print_status_report(cl)
    actions.active_sweep(cl)
    
    sys_log.info("🛡️ 防護系統已上線，主迴圈監聽中...")
    cl.revision = cl.getLastOpRevision()
    last_log_time = time.time()

    import threading

    def background_sweep():
        import random
        while True:
            sleep_time = random.uniform(config.REPORT_INTERVAL_MIN, config.REPORT_INTERVAL_MAX)
            time.sleep(sleep_time)
            try:
                dashboard.print_status_report(cl)
                actions.active_sweep(cl)
            except Exception as e:
                error_log.error(f"⚠️ 背景巡邏發生異常: {e}")

    # 啟動背景巡邏執行緒
    sweep_thread = threading.Thread(target=background_sweep, daemon=True)
    sweep_thread.start()

    while True:
        try:
            # 即時事件監聽 (改用 sync 替代被拔除的 fetchOps)
            try:
                ops_res = cl.sync(cl.revision)
                # sync 回傳的是一個 dict，裡面包含 operations
                ops = safe_get(ops_res, 'operations', 1) or []
            except Exception as e:
                if "fetchOps" in str(e) or "sync" in str(e):
                    # 如果連 sync 都不支援，降級為靜默，純靠 active_sweep
                    ops = []
                else:
                    raise e
                    
            for op in ops:
                cl.revision = max(cl.revision, op[1] if isinstance(op, list) else safe_get(op, 'revision', 1))
                op_type = op[3] if isinstance(op, list) else safe_get(op, 'type', 3)

                # 攔截群組邀請 (Op 13, 124)
                if op_type in [13, 124]:
                    group_id = op[10] if isinstance(op, list) else safe_get(op, 'param1', 10)
                    param3 = op[12] if isinstance(op, list) else safe_get(op, 'param3', 12)
                    invited_mids = param3.split('\x1e') if isinstance(param3, str) else (param3 if isinstance(param3, list) else [param3])
                    
                    for mid in invited_mids:
                        if not mid: continue
                        contact = cl.getContact(mid)
                        if contact:
                            real_name = safe_get(contact, 'displayName', 22)
                            action_log.info(f"🔍 [即時雷達] 偵測到邀請，被邀者: 「{real_name}」")
                            
                            if real_name == config.TARGET_NAME:
                                action_log.warning(f"⚠️ [即時雷達] 警報！目標 [{config.TARGET_NAME}] 被邀請！")
                                actions.execute_ban(cl, group_id, mid, real_name, "cancel")

                # 發現入群 (Op 17, 130)
                elif op_type in [17, 130]:
                    group_id = op[10] if isinstance(op, list) else safe_get(op, 'param1', 10)
                    joined_mid = op[11] if isinstance(op, list) else safe_get(op, 'param2', 11)
                    contact = cl.getContact(joined_mid)
                    
                    if contact:
                        real_name = safe_get(contact, 'displayName', 22)
                        action_log.info(f"🔍 [即時雷達] 偵測到加入，入群者: 「{real_name}」")
                        
                        if real_name == config.TARGET_NAME:
                            action_log.warning(f"⚠️ [即時雷達] 警報！目標 [{config.TARGET_NAME}] 闖入群組！")
                            actions.execute_ban(cl, group_id, joined_mid, real_name, "kick")
                            
        except Exception as e:
            # 發生錯誤（通常是 token 過期引發的 401 拒絕存取）
            error_log.error(f"⚠️ 主迴圈發生異常: {e}")
            if auth.try_refresh_token(cl):
                # 續命成功後，重置 revision，繼續監聽
                try:
                    cl.revision = cl.getLastOpRevision()
                except:
                    pass
            else:
                # 若無法續命，只能等待 10 秒後再試，避免無意義的洗畫面
                time.sleep(10)

        time.sleep(1)

if __name__ == "__main__":
    run_bot()