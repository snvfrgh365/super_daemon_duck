# actions.py
import time
import config
from logger import action_log, error_log

def execute_ban(cl, group_id, target_mid, target_name, action_type):
    """標準化制裁流程：冷卻 -> 封鎖 -> 間隔 -> 踢除/取消 (隱形移除法)"""
    # 確保 group_id 與 mid 都是字串（CHRLINE API 內部會呼叫 len()，int 會炸掉）
    group_id = str(group_id)
    target_mid = str(target_mid)
    
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

def active_sweep(cl):
    """無差別主動掃描：檢查所有群組，發現目標直接處置"""
    from dashboard import safe_get, extract_all_user_mids
    try:
        chat_res = cl.getAllChatMids()
        gids = safe_get(chat_res, 'memberChatMids', 1)
        if gids is None:
            gids = chat_res
        if not isinstance(gids, list): gids = list(gids)
        if not gids: return

        chats_res = cl.getChats(gids, withMembers=True)
        chats = safe_get(chats_res, 'chats', 1)
        if chats is None:
            chats = chats_res
        if not isinstance(chats, list): chats = list(chats)

        for chat in chats:
            # chatMid 在 thrift key 2（key 1 是群組類型 int）
            group_id = safe_get(chat, 'chatMid', 2)
            if not group_id: continue

            all_mids = extract_all_user_mids(chat)
            if all_mids:
                contacts_res = cl.getContacts(all_mids)
                contacts = safe_get(contacts_res, 'contacts', 1) or contacts_res
                if not isinstance(contacts, list): contacts = list(contacts)

                for c in contacts:
                    name = safe_get(c, 'displayName', 22) or ""
                    mid = safe_get(c, 'mid', 1) or safe_get(c, 'contactMid', 1)
                    
                    if name == config.TARGET_NAME and mid:
                        # 確保 mid 是字串
                        mid = str(mid)
                        action_log.warning(f"🚨 [主動掃描] 發現目標 [{name}] 潛伏於群組中！")
                        execute_ban(cl, group_id, mid, name, "kick")
    except Exception:
        pass