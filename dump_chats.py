import os
import sys
import io
import time
import config
from CHRLINE import CHRLINE

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run():
    with open(config.TOKEN_FILE, "r") as f:
        token = f.read().strip()
        
    cl = CHRLINE(
        token,
        device="DESKTOPMAC",
        version="8.4.1.3286",
        os_name="MAC",
        os_version="12.0"
    )
    
    print("\n--- 1. getAllChatMids ---")
    chat_res = cl.getAllChatMids()
    print(chat_res)
    
    from dashboard import safe_get
    gids = safe_get(chat_res, 'memberChatMids', 1) or chat_res
    if not isinstance(gids, list):
        gids = list(gids)
    print("\ngids:", gids)
    
    if gids:
        print("\n--- 2. getChats ---")
        try:
            chats_res = cl.getChats(gids, withMembers=True)
            print("withMembers=True response:")
            print(chats_res)
        except Exception as e:
            print("getChats(withMembers=True) failed:", e)
            
if __name__ == "__main__":
    run()
