import os
import sys
import io
import time
import json
import config
from CHRLINE import CHRLINE

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run():
    print("="*50)
    print("🔍 API Structure Audit Tool")
    print("="*50)
    
    with open(config.TOKEN_FILE, "r") as f:
        token = f.read().strip()
        
    try:
        cl = CHRLINE(
            token,
            device="DESKTOPMAC",
            version="8.4.1.3286",
            os_name="MAC",
            os_version="12.0"
        )
        print("✅ Client Initialized.\n")
    except Exception as e:
        print("❌ Failed to initialize client:", e)
        return

    # 1. getProfile
    try:
        print("--- [1] getProfile() ---")
        print(cl.getProfile())
        print()
    except Exception as e:
        print("❌ getProfile() failed:", e)

    # 2. getAllChatMids
    gids = []
    try:
        print("--- [2] getAllChatMids() ---")
        chat_res = cl.getAllChatMids()
        print(chat_res)
        
        # Extraction logic simulation
        from dashboard import safe_get
        gids_extracted = safe_get(chat_res, 'memberChatMids', 1)
        if gids_extracted is None:
            gids_extracted = chat_res
        if not isinstance(gids_extracted, list):
            gids_extracted = list(gids_extracted)
            
        gids = gids_extracted
        print("-> Parsed GIDs:", gids)
        print()
    except Exception as e:
        print("❌ getAllChatMids() failed:", e)
        
    # 3. getChats
    try:
        print("--- [3] getChats(withMembers=True) ---")
        if not gids:
            print("⚠️ Skipping getChats because no GIDs were found (Bot is in 0 groups).")
        else:
            chats_res = cl.getChats(gids, withMembers=True)
            print(chats_res)
            
            chats = safe_get(chats_res, 'chats', 1)
            if chats is None:
                chats = chats_res
            if not isinstance(chats, list):
                chats = list(chats)
                
            print("-> Parsed Chats Count:", len(chats))
            
            if chats:
                print("-> Structure of first chat:")
                chat = chats[0]
                print(chat)
                
                # Check where memberMids actually are
                extra = safe_get(chat, 'extra', 5)
                group_extra = safe_get(extra, 'groupExtra', 1) if extra else None
                member_mids = safe_get(group_extra, 'memberMids', 1) if group_extra else None
                print("-> Extracted memberMids:", member_mids)
        print()
    except Exception as e:
        print("❌ getChats() failed:", e)

    # 4. sync
    try:
        print("--- [4] sync() ---")
        rev = cl.getLastOpRevision()
        print("-> Current Revision:", rev)
        
        ops_res = cl.sync(rev)
        print("-> Sync Response:")
        print(ops_res)
        
        ops = safe_get(ops_res, "operations", 1)
        if ops is None:
            ops = ops_res
        if not isinstance(ops, list):
            ops = list(ops)
        print(f"-> Found {len(ops)} operations.")
    except Exception as e:
        print("❌ sync() failed:", e)

if __name__ == "__main__":
    run()
