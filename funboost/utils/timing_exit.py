


import os
import time

def exit_after(seconds=30,status=0):
    time.sleep(seconds)
    os._exit(status)
