#!/usr/bin/env python

from daemon import runner
from novaevacuate.app import manage
import time

class MyDaemon(object):
    def __init__(self):
        self.stdin_path = '/dev/null'
	self.stdout_path = '/dev/null'
	self.stderr_path = '/dev/null'
	self.pidfile_path = '/tmp/nova_evacuate.pid'
	self.pidfile_timeout = 5
    def run(self):
        while True:
            manage.manager()
	    time.sleep(30)

my_daemon = MyDaemon()
daemon_runner = runner.DaemonRunner(my_daemon)
daemon_runner.do_action()

