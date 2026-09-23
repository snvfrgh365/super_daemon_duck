import os
import sys
import io
import time
import config
from CHRLINE import CHRLINE
import dashboard

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
    
    dashboard.print_status_report(cl, time.time())

if __name__ == "__main__":
    run()
