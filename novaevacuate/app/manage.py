import time
import sys
sys.path.append("..")
from novacheck.network.network import get_net_status as network_check
from novacheck.network.network import leader
from novacheck.service.service import get_service_status as service_check
#import fence_agent
import fence_agent
from log import logger

class item:
    def __init__(self):
        self.node = "null"
        self.name = "null"
        self.status = "null"
        self.ip = "null"

def start(name):
    logger.info("Service %s start" % (name))
    manager()



def manager():
    while(1):
        if leader() == "true":
            print "leader"
            logger.info("Start check.....")
            net_checks = network_check()
            ser_checks = service_check()
        else:
            time.sleep(10)
            pass
        for net_check in net_checks:
            network = item()
            network.node = net_check['name']
            network.name = net_check['net_role']
            network.status = net_check['status']
            network.ip = net_check['addr']
            if network.status == "true":
                print network.node, network.name, network.status,network.ip
                logger.info("%s %s status is: %s (%s)" %(network.node, network.name, network.status,network.ip))
            else:
                print network.node, network.name, network.status,network.ip
                
                logger.error("%s %s status is: %s (%s)" % (network.node, network.name, network.status,network.ip))
                fence_agent.FenceCheck.network_recovery(network.node, network.name)
        time.sleep(10)
"""
        for ser_check in ser_checks:
            service = item()
            service.node = ser_check['node-name']
            service.name = ser_check['']
            service.status = ser_check['status']
            if service.status == "ok":
                print service.node, service.name, service.status
                logger.info("%s %s status is: %s" %(service.node, service.name, service.status))
            else:
                print service.node, service.name, service.status
                logger.error("%s %s status is: %s" % (service.node, service.name, service.status))
                fence = fence_agent.FenceCheck.service_recovery(service.node, service.name)

        time.sleep(30)
"""
#manager()
