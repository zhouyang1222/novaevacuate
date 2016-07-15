import commands
from novaevacuate.log import logger
from novaevacuate.openstack_novaclient import NovaClientObj as nova_client

class NovaCompute(object):
    def __init__(self):
        self.compute = nova_client.get_compute()[1]

    def service_status(self):
        # status is list example: [{'status': 'up', 'node-name': 'node1', 'type': 'nova-compute'},
        # {'status': 'down', 'node-name': 'node-2', 'type': 'nova-compute'}]

        logger.info("openstack-nova-compute service start check")
        novacompute = []
        for i in self.compute:
            error_compute = []
            if i not in error_compute:
                (s, o) = commands.getstatusoutput("ssh '%s' systemctl -a|grep openstack-nova-compute" % (i))
                if s == 0 and o != None:
                    if 'running' in o and 'active' in o:
                        novacompute.append({"node-name": i,"status": "active", "datatype": "novacompute"})
                    elif 'dead' in o and 'inactive' in o:
                        novacompute.append({"node-name": i,"status": "dead", "datatype": "novacompute"})
                    elif 'failed' in o:
                        novacompute.append({"node-name": i,"status": "failed", "datatype": "novacompute"})
                else:
                    novacompute.append({"node-name": i,"status": "unknown", "datatype": "novacompute"})
                    error_compute.append(i)
                    logger.warn("%s openstack-nova-compute service unknown" % i)
        return novacompute

    def nova_recovery(self, node):
        logger.info("openstack-nova-compute service start recovery")
        try:
            commands.getoutput("ssh '%s' systemctl restart openstack-nova-compute")
        except Exception as e:
            logger.error(e)

    def nova_stop(self, node):
        logger.info("openstack-nova-compute service will be stop")
        try:
            commands.getoutput("ssh '%s' systemctl stop openstack-nova-compute")
        except Exception as e:
            logger.error(e)

class NovaService(object):
    def service_check(self):
        novaservice = []
        services = nova_client.get_compute()[0]

        if not services:
            logger.warn("Service could not be found nova-compute")
        else:
            count = len(services)
            counter = 0
            while counter < count:
                service = services[counter]
                host = service.host
                if service.status == "enabled" and service.state == "up":
                    novaservice.append({"node-name": host,"status": "up", "datatype": "novaservice"})
                elif service.status == "disabled":
                    if service.binary == "nova-compute" and service.disabled_reason:
                        novaservice.append({"node-name": host,"status": "up", "datatype": "novaservice"})

                    novaservice.append({"node-name": host,"status": "down", "datatype": "novaservice"})
                elif service.state == "down":
                    novaservice.append({"node-name": host,"status": "down", "datatype": "novaservice"})
                else:
                    logger.error("nova compute on host %s is in an unknown State" % (service.host))
                counter += 1
            return novaservice

    def service_recovery(self, node, name):
        nova_client.nova_service_enable(node)
        logger.info("%s nova-compute service is enabled.")

    def service_fence(self,node):
        nova_client.nova_service_disable(node)
        logger.warn("%s nova-compute service is disabled."
                    "Nova cloud not create instance in %s" % (node, node))

def get_service_status():
    nova_status = []
    n_c = NovaCompute()
    n_s = NovaService()

    for i in n_c.service_status():
        nova_status.append(i)

    for n in n_s.service_check():
        nova_status.append(n)

    return nova_status

