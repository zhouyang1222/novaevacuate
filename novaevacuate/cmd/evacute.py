from novaevacuate.app import manage
import time

def start():
    manage.manager()

while True:
    try:
        start()
        time.sleep(30)
    except:
        pass