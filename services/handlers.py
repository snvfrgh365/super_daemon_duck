# handlers.py
import threading
from services import actions
from services import targets
from core.line_constants import OpType, OpField, ContactField
from utils.helpers import safe_get
from core.logger import action_log, error_log

def handle_operation(cl, op):
    """
    事件分發器 (Event Dispatcher)
    負責解析 LINE 的 operation 並分發到對應的處理邏輯
    """
    try:
        op_type = op[OpField.TYPE] if isinstance(op, list) else safe_get(op, "type", OpField.TYPE)

        # 攔截群組邀請 (Op 13, 124)
        if op_type in [OpType.NOTIFIED_INVITE_INTO_GROUP, OpType.NOTIFIED_INVITE_INTO_CHAT]:
            _handle_invite(cl, op)

        # 發現入群 (Op 17, 130)
        elif op_type in [OpType.NOTIFIED_ACCEPT_GROUP_INVITATION, OpType.NOTIFIED_ACCEPT_CHAT_INVITATION]:
            _handle_join(cl, op)
            
    except Exception as e:
        error_log.error(f"解析事件發生錯誤: {e}")

def _execute_ban_async(cl, group_id, target_mid, target_name, action_type):
    """將踢人/取消邀請丟到背景執行，避免阻塞主監聽迴圈"""
    thread = threading.Thread(
        target=actions.execute_ban,
        args=(cl, group_id, target_mid, target_name, action_type),
        daemon=True
    )
    thread.start()

def _handle_invite(cl, op):
    group_id = op[OpField.PARAM1] if isinstance(op, list) else safe_get(op, "param1", OpField.PARAM1)
    param3 = op[OpField.PARAM3] if isinstance(op, list) else safe_get(op, "param3", OpField.PARAM3)
    sep = "\x1e"
    invited_mids = param3.split(sep) if isinstance(param3, str) else (param3 if isinstance(param3, list) else [param3])

    for mid in invited_mids:
        if not mid: continue
        contact = cl.getContact(str(mid))
        if contact:
            real_name = safe_get(contact, "displayName", ContactField.DISPLAY_NAME)
            action_log.info("[即時雷達] 偵測到邀請，被邀者: %s" % real_name)
            
            if targets.is_target(real_name, mid):
                bot_mid = str(getattr(cl.profile, "mid", "")) if hasattr(cl, "profile") else ""
                if str(mid) == bot_mid:
                    continue
                action_log.warning("[即時雷達] 警報！目標 [%s] 被邀請！" % real_name)
                _execute_ban_async(cl, group_id, mid, real_name, "cancel")

def _handle_join(cl, op):
    group_id = op[OpField.PARAM1] if isinstance(op, list) else safe_get(op, "param1", OpField.PARAM1)
    joined_mid = op[OpField.PARAM2] if isinstance(op, list) else safe_get(op, "param2", OpField.PARAM2)
    
    if not joined_mid: return
        
    contact = cl.getContact(str(joined_mid))
    if contact:
        real_name = safe_get(contact, "displayName", ContactField.DISPLAY_NAME)
        action_log.info("[即時雷達] 偵測到加入，入群者: %s" % real_name)
        
        if targets.is_target(real_name, joined_mid):
            bot_mid = str(getattr(cl.profile, "mid", "")) if hasattr(cl, "profile") else ""
            if str(joined_mid) == bot_mid:
                return
            action_log.warning("[即時雷達] 警報！目標 [%s] 闖入群組！" % real_name)
            _execute_ban_async(cl, group_id, joined_mid, real_name, "kick")
