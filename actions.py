# actions.py
import time
import config
from logger import action_log, error_log

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

            extra = safe_get(chat, 'extra', 8) or {}
            
            # 取得實際群組成員
            member_mids = safe_get(extra, 'memberMids', 1) or {}
            if isinstance(member_mids, dict): member_mids = list(member_mids.keys())
            elif not isinstance(member_mids, list): member_mids = list(member_mids)
            
            # 取得受邀尚未加入者
            invitee_mids = safe_get(extra, 'inviteeMids', 2) or {}
            if isinstance(invitee_mids, dict): invitee_mids = list(invitee_mids.keys())
            elif not isinstance(invitee_mids, list): invitee_mids = list(invitee_mids)
            
            all_mids = list(set(member_mids + invitee_mids))
            
            if all_mids:
                contacts_res = cl.getContacts(all_mids)
                contacts = safe_get(contacts_res, 'contacts', 1) or contacts_res
                if not isinstance(contacts, list): contacts = list(contacts)

                for c in contacts:
                    name = safe_get(c, 'displayName', 22) or ""
                    mid = safe_get(c, 'mid', 1) or safe_get(c, 'contactMid', 1)
                    
                    if name == config.TARGET_NAME and mid:
                        mid = str(mid)
                        bot_mid = str(getattr(cl.profile, "mid", "")) if hasattr(cl, "profile") else ""
                        
                        # 如果目標是自己，就直接略過，避免無限迴圈洗版
                        if mid == bot_mid:
                            continue
                            
                        # 判斷要踢除還是取消邀請
                        if mid in member_mids:
                            action_log.warning(f"🚨 [主動掃描] 發現目標 [{name}] 潛伏於群組中！")
                            execute_ban(cl, group_id, mid, name, "kick")
                        elif mid in invitee_mids:
                            action_log.warning(f"🚨 [主動掃描] 發現目標 [{name}] 正在受邀名單中！")
                            execute_ban(cl, group_id, mid, name, "cancel")
    except Exception:
        pass