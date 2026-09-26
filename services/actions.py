# actions.py
import time
from core import config
from core.logger import action_log, error_log

def execute_ban(cl, group_id, target_mid, target_name, action_type):
    """標準化制裁流程：冷卻 -> 封鎖 -> 間隔 -> 踢除/取消 (隱形移除法)"""
    # 確保 group_id 與 mid 都是字串
    group_id = str(group_id)
    target_mid = str(target_mid)
    
    # 絕對防禦：禁止機器人踢除/封鎖自己
    bot_mid = str(getattr(cl.profile, "mid", "")) if hasattr(cl, "profile") else ""
    if target_mid == bot_mid:
        action_log.warning(f"⚠️ [保護機制] 偵測到目標為機器人自身 ({target_name})，已強制取消制裁動作。")
        return

    action_log.info(f"⏳ [執行制裁] 準備處置 {target_name}，系統冷卻 {config.ACTION_COOLDOWN} 秒...")
    time.sleep(config.ACTION_COOLDOWN)
    
    # 步驟 1：將對方封鎖
    try:
        cl.blockContact(target_mid)
        action_log.info(f"🛑 [封鎖] 步驟 1/2：已將 [{target_name}] 加入黑名單")
    except Exception as e:
        error_log.error(f"❌ 封鎖失敗: {e}")
        
    time.sleep(config.API_DELAY)
    
    # 步驟 2：執行踢除或取消邀請
    if action_type == "cancel":
        try:
            # CHRLINE cancelChatInvitation(to, mid) 第二個參數是單一字串，不是 list
            cl.cancelChatInvitation(group_id, target_mid)
            action_log.info(f"🛡️ [取消] 步驟 2/2：已取消 [{target_name}] 的群組邀請")
        except Exception as e:
            error_log.error(f"❌ 取消邀請失敗: {e}")
    else:
        try:
            # CHRLINE deleteOtherFromChat(to, mid) 第二個參數是單一字串，不是 list
            cl.deleteOtherFromChat(group_id, target_mid)
            action_log.info(f"💥 [隱形踢除] 步驟 2/2：已將 [{target_name}] 強制移出群組！")
        except Exception as e:
            error_log.error(f"❌ 踢除失敗: {e}")

def active_sweep(cl, state):
    """無差別主動掃描：檢查所有群組，發現目標直接處置"""
    try:
        from services import targets
        for group in state:
            group_id = group.get("group_id")
            if not group_id: continue
            
            # 檢查 members
            for member in group.get("members", []):
                mid = member.get("mid")
                name = member.get("name")
                if targets.is_target(name, mid) and mid:
                    bot_mid = str(getattr(cl.profile, "mid", "")) if hasattr(cl, "profile") else ""
                    if mid == bot_mid:
                        continue
                    action_log.warning(f"🚨 [主動掃描] 發現目標 [{name}] 潛伏於群組中！")
                    execute_ban(cl, group_id, mid, name, "kick")
                    
            # 檢查 invitees
            for invitee in group.get("invitees", []):
                mid = invitee.get("mid")
                name = invitee.get("name")
                if targets.is_target(name, mid) and mid:
                    bot_mid = str(getattr(cl.profile, "mid", "")) if hasattr(cl, "profile") else ""
                    if mid == bot_mid:
                        continue
                    action_log.warning(f"🚨 [主動掃描] 發現目標 [{name}] 正在受邀名單中！")
                    execute_ban(cl, group_id, mid, name, "cancel")
    except Exception as e:
        error_log.error(f"active_sweep error: {e}")