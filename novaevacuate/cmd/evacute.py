from novaevacuate.app import manage
import time
import os
import sys
import signal

def start():
    manage.manager()

def main():
    pid = os.fork()
    if (pid == 0):
        os.setsid()

        pid = os.fork()
        if (pid == 0):
            os.chdir("/")
            os.umask(0)

            while True:
                start()
                time.sleep(30)
        else:
            os._exit(0)
    else:
        os._exit(0)

if __name__ == "__main__":
    main()