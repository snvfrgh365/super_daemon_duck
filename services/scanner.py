from utils.helpers import safe_get
from core.line_constants import SyncResponseField, ChatField, ChatExtraField, GroupExtraField, ContactField

def fetch_group_state(cl):
    """
    獲取目前所有群組及其成員名單（Single Source of Truth）。
    回傳值: 陣列包含各群組的字典資訊。
    """
    state = []
    try:
        chat_res = cl.getAllChatMids()
        gids = safe_get(chat_res, 'memberChatMids', SyncResponseField.MEMBER_CHAT_MIDS)
        if gids is None:
            gids = chat_res
        if not isinstance(gids, list): gids = list(gids)
        if not gids: return state

        try:
            chats_res = cl.getChats(gids, withMembers=True)
        except Exception:
            chats_res = cl.getChats(gids)
            
        chats = safe_get(chats_res, 'chats', 1)
        if chats is None:
            chats = chats_res
        if not isinstance(chats, list): chats = list(chats)

        for chat in chats:
            group_id = safe_get(chat, 'chatMid', ChatField.CHAT_MID)
            if not group_id: continue
            
            group_name = safe_get(chat, 'chatName', ChatField.CHAT_NAME) or "未命名群組"

            extra = safe_get(chat, 'extra', ChatField.EXTRA) or {}
            group_extra = safe_get(extra, 'groupExtra', ChatExtraField.GROUP_EXTRA) or {}
            
            member_mids = safe_get(group_extra, 'memberMids', GroupExtraField.MEMBER_MIDS) or {}
            if isinstance(member_mids, dict): member_mids = list(member_mids.keys())
            elif not isinstance(member_mids, list): member_mids = list(member_mids)
            
            invitee_mids = safe_get(group_extra, 'inviteeMids', GroupExtraField.INVITEE_MIDS) or {}
            if isinstance(invitee_mids, dict): invitee_mids = list(invitee_mids.keys())
            elif not isinstance(invitee_mids, list): invitee_mids = list(invitee_mids)
            
            all_mids = list(set(member_mids + invitee_mids))
            
            members_data = []
            invitees_data = []
            
            if all_mids:
                contacts_res = cl.getContacts(all_mids)
                contacts = safe_get(contacts_res, 'contacts', 1) or contacts_res
                if not isinstance(contacts, list): contacts = list(contacts)

                for c in contacts:
                    name = safe_get(c, 'displayName', ContactField.DISPLAY_NAME) or ""
                    mid = safe_get(c, 'mid', ContactField.MID) or safe_get(c, 'contactMid', ContactField.MID)
                    if not mid: continue
                    mid = str(mid)
                    
                    user_info = {"mid": mid, "name": name}
                    if mid in member_mids:
                        members_data.append(user_info)
                    elif mid in invitee_mids:
                        invitees_data.append(user_info)
                        
            state.append({
                "group_id": group_id,
                "group_name": group_name,
                "members": members_data,
                "invitees": invitees_data
            })
            
    except Exception as e:
        from core.logger import error_log
        error_log.error(f"獲取群組狀態失敗: {e}")
        
    return state
