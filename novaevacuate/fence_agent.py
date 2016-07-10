# fence agent have three fence status
# 1. Power fencing
# 2. Fencing from storage in Cinder
# 3. Fencing from network in Neutron
# 4. Self fencing by Nova Compute

import datetime
import commands
from novaevacuate.novacheck.network.network import get_net_status
from novaevacuate.novacheck.service.service import get_service_status
from novaevacuate.log import logger
import novaclient
from novaclient import client
from novaevacuate.credentials import get_nova_credentials_v2
import time

count = 3
"""def task_period():
    task_time = {"New_time": None, "Old_time": None}
    task_ttl = 30
    start_time = datetime.datetime.now()
    end_time = datetime.datetime.now()
    time_result = (end_time - start_time).second
    if time_result >= 30:
        task_time["Old_time"] = end_time
        return True
    else:

        pass

"""


class FenceCheck(object):
    def __init__(self, node, name):
        self.node = node
        self.name = name

    def network_recovery(self, node, name):
        while count < 3:
            time.sleep(10)
        commands.getoutput("ssh %s ifup %s" % (node, name))
        network = network_check()
        if network.status == "ok":
            logger.info("%s %s recovery Success" % (node, name))
        else:
            self.instance_evacute(node)

    def service_recovery(self, node, name):
        pass

    def instance_evacute(self, node):
        pass