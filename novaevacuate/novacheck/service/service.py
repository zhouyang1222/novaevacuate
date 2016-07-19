import commands
import time
from novaevacuate.log import logger
from novaevacuate.openstack_novaclient import NovaClientObj as nova_client
from novaevacuate.fence_agent import Fence


class NovaService(object):

    def __init__(self):
        self.compute = nova_client.get_compute()[1]
        self.service = nova_client.get_compute()[0]

    # use systemctl check openstack-nova-compute service message
    def sys_compute(self):
        # status is list example: [{'status': 'up', 'node-name': 'node1', 'type':
        # 'nova-compute'},
        # {'status': 'down', 'node-name': 'node-2', 'type': 'nova-compute'}]

        logger.info("openstack-nova-compute service start check")
        sys_com = []
        for i in self.compute:
            (s, o) = commands.getstatusoutput("ssh '%s' systemctl -a|grep \
                                                openstack-nova-compute" % (i))
            if s == 0 and o != None:
                if 'running' in o and 'active' in o:
                    sys_com.append({"node-name": i,"status": True, "datatype": "novacompute"})
                elif 'dead' in o and 'inactive' in o:
                    sys_com.append({"node-name": i,"status": False, "datatype": "novacompute"})
                elif 'failed' in o:
                    sys_com.append({"node-name": i,"status": False, "datatype": "novacompute"})
            else:
                sys_com.append({"node-name": i,"status": "unknown", "datatype": "novacompute"})
                logger.warn("%s openstack-nova-compute service unknown" % i)
        return sys_com

    # use novaclient check nova-compute status and state message
    def ser_compute(self):
        logger.info("nova-compute status and state start check")

        ser_com = []
        services = self.service
        if not services:
            logger.warn("Service could not be found nova-compute")
        else:
            count = len(services)
            counter = 0
            while counter < count:
                service = services[counter]
                host = service.host
                if service.status == "enabled" and service.state == "up":
                    ser_com.append({"node-name": host,"status": True, "datatype": "novaservice"})
                elif service.status == "disabled":
                    if service.binary == "nova-compute" and service.disabled_reason:
                        ser_com.append({"node-name": host,"status": True, "datatype": "novaservice"})
                    ser_com.append({"node-name": host,"status": False, "datatype": "novaservice"})
                elif service.state == "down":
                    ser_com.append({"node-name": host,"status": False, "datatype": "novaservice"})
                else:
                    logger.error("nova compute on host %s is in an unknown State" % (service.host))
                counter += 1
            return ser_com

def get_service_status():
    nova_status = []
    ns = NovaService()
    for i in ns.sys_compute():
        nova_status.append(i)

    for n in ns.ser_compute():
        nova_status.append(n)

    return nova_status

def novaservice_retry(node, type):
    ns = NovaService()
    fence = Fence()
    if type == "novaservice":
        for i in range(3):
            logger.warn("%s %s start retry %d check" % (node, type, i))
            status = ns.ser_compute()
            time.sleep(10)

        # get retry check status
        for n in status:
            if False in n.values():
                fence.compute_fence(node)

    elif type == "novacompute":
        for i in range(3):
            logger.warn("%s %s start retry %d check" % (node, type, i))
            status = ns.sys_compute()
            time.sleep(10)

        # get retry check status
        for n in status:
            if False in n.values():
                fence.compute_fence(node)