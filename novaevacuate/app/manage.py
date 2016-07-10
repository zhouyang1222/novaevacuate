import time
from novaevacuate.novacheck.network.network import get_net_status as network_check
from novaevacuate.novacheck.network.network import leader
from novaevacuate.novacheck.service.service import get_service_status as service_check
from novaevacuate import fence_agent
from novaevacuate.log import logger

def start(name):
    logger.info("Service %s start" % (name))
    manager()



def manager():
    while(1):
        if leader() == "true":
            logger.info("Start check.....")
            net_checks = network_check()
            ser_checks = service_check()
        else:
            time.sleep(30)
            pass
        for net_check in net_checks:
            network.node = net_check['name']
            network.name = net_check['net_role']
            network.status = net_check['status']
            network.ip = net_check['addr']
            if network.status == "ok":
                logger.info("%s %s status is: %s" %(network.node, network.name, network.status,network.ip))
            else:
                logger.error("%s %s status is: %s" % (network.node, network.name, network.status,network.ip))
                fence = fence_agent.FenceCheck.network_recovery(network.node, network.name)

        for ser_check in ser_checks:
            service.node = ser_check['node-name']
            service.name = ser_check['']
            service.status = ser_check['status']
            if service.status == "ok":
                logger.info("%s %s status is: %s" %(service.node, service.name, service.status))
            else:
                logger.error("%s %s status is: %s" % (service.node, service.name, service.status))
                fence = fence_agent.FenceCheck.service_recovery(service.node, service.name)

        time.sleep(30)

