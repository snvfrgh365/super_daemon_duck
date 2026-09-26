# line_constants.py
# 統一定義 LINE API 與 Thrift 封包的各種 Magic Numbers 與欄位 ID

class OpType:
    """LINE 接收到的事件類型 (Operations)"""
    NOTIFIED_INVITE_INTO_GROUP = 13
    NOTIFIED_INVITE_INTO_CHAT = 124
    NOTIFIED_ACCEPT_GROUP_INVITATION = 17
    NOTIFIED_ACCEPT_CHAT_INVITATION = 130

class OpField:
    """Operation 封包內的欄位 ID"""
    REVISION = 1
    TYPE = 3
    PARAM1 = 10  # 通常是群組 ID
    PARAM2 = 11  # 通常是觸發事件的人 (入群者、邀請人)
    PARAM3 = 12  # 通常是被操作的目標 (被邀請者)

class ChatField:
    """群組/聊天室 (Chat) 的欄位 ID"""
    CHAT_MID = 2
    CHAT_NAME = 6
    EXTRA = 8

class ChatExtraField:
    """群組擴充資訊 (ChatExtra) 的欄位 ID"""
    GROUP_EXTRA = 1

class GroupExtraField:
    """群組成員資訊 (GroupExtra) 的欄位 ID"""
    MEMBER_MIDS = 4
    INVITEE_MIDS = 5

class ContactField:
    """聯絡人/使用者 (Contact) 的欄位 ID"""
    MID = 1
    DISPLAY_NAME = 22

class SyncResponseField:
    """GetAllChatMids 回應的欄位 ID"""
    MEMBER_CHAT_MIDS = 1
    INVITED_CHAT_MIDS = 2
