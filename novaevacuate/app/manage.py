import time
from novaevacuate.novacheck.network.network import get_net_status as network_check
from novaevacuate.novacheck.network.network import leader
from novaevacuate.novacheck.network.network import network_recovery
from novaevacuate.novacheck.service.service import get_service_status as service_check
from novaevacuate.novacheck.service.service import recovery
from novaevacuate import fence_agent
from novaevacuate.log import logger

fenced_nodes = []
class item:
    def __init__(self):
        self.node = "null"
        self.name = "null"
        self.status = "null"
        self.ip = "null"


def manager():
    if leader() == "true":
        logger.info("Start check.....")
        net_checks = network_check()
        ser_checks = service_check()
        if not net_checks and not ser_checks:
            fenced_nodes = []
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
            logger.info("%s %s status is: %s (%s)" %(network.node, network.name,
                                                     network.status,network.ip))
        else:
            flag = 0
            for fenced_node in fenced_nodes:
                if network.node == fenced_node:
                    logger.info("%s is fenced" %fenced_node)
                    flag = 1
                    break
            if flag == 0:
                logger.error("%s %s status is: %s (%s)" % (network.node, network.name,
                                                           network.status,network.ip))
                fence = network_recovery(network.node, network.name)

    for ser_check in ser_checks:
        service = item()
        service.node = ser_check['node-name']
        service.name = ser_check['datatype']
        service.status = ser_check['status']
        if service.status == True:
            logger.info("%s %s status is: %s" %(service.node, service.name,
                                                service.status))
        elif service.status == False or service.status == "unknown":
            flag = 0
            for fenced_node in fenced_nodes:
                if network.node == fenced_node:
                    logger.info("%s is fenced" %fenced_node)
                    flag = 1
                    break
            if flag == 0:
                logger.error("%s %s status is: %s" % (service.node, service.name,
                                                      service.status))
                fence = recovery(service.node, service.name)

