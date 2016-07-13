import sys
import re
import commands
import novaclient
from novaclient import client
from novaevacuate.credentials import get_nova_credentials_v2
from novaevacuate.log import logger

#program exit stat define
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

def get_compute():
    creds = get_nova_credentials_v2()
    nova = client.Client(**creds)
    try:
        services = nova.services.list(binary="nova-compute")
    except novaclient.exceptions.Unauthorized:
       logger.warn("Failed to authenticate to Keystone")
    except Exception:
        logger.warn("Failed to query service")

    node_count = len(services)
    counter = 0
    node_name = []

    while counter < node_count:
        service = services[counter]
        node_name.append(service.host)
        counter+=1

    return services, node_name

class NovaCompute():
    def __init__(self):
        self.compute = get_compute()[1]

    def service_status(self):
        # status is list example: [{'status': 'up', 'node-name': 'node1', 'type': 'nova-compute'},
        # {'status': 'down', 'node-name': 'node-2', 'type': 'nova-compute'}]

        logger.info("openstack-nova-compute service start check")
        novacompute = []
        for i in self.compute:
            (s, o) = commands.getstatusoutput("ssh '%s' systemctl -a|grep openstack-nova-compute" % (i))
            if s == 0 and o != None:
                service_status = o
                #if re.search('runing', service_status) and re.search('active', service_status):
                if 'running' in o and 'active' in o:
                    novacompute.append({"node-name": i,"status": "active", "datatype": "novacompute"})
                #elif re.search('dead', service_status) and re.search('inactive', service_status):
                elif 'dead' in o and 'inactive' in o:
                    novacompute.append({"node-name": i,"status": "dead", "datatype": "novacompute"})
                #elif re.search('faild', service_status):
                elif 'failed' in o:
                    novacompute.append({"node-name": i,"status": "failed", "datatype": "novacompute"})
            else:
                novacompute.append({"node-name": i,"status": "unknown", "datatype": "novacompute"})
                logger.warn("%s openstack-nova-compute service unknown" % i)
            for n in novacompute:
                status = n["status"]
            logger.info("openstack-nova-compute in %s is %s" % (i, status) )
        return novacompute

#    def service_active(self, compute):
#       service_status = self.service_status()
#        if service_status['state'] == HOST_DEAD or \
#                        service_status == HOST_FAILD:
#            commands.getoutput("systemctl restart openstack-nova-compute")
#        service_status = self.service_status()
#        if service_status['state'] == HOST_DEAD or \
#                        service_status == HOST_FAILD:
#            self.service_report()

#    def service_report(self, mail):
#        pass

#    def service_evacute(self, EVACUTE):
#        pass


class NovaService():
    def __init__(self):
        pass

    def service_check(self):
        novaservice = []
        services = get_compute()[0]

        logger.info("nova-compute service check start")
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
                    # print ("nova compute service on host %s is OK " % (HOST))
                elif service.status == "disabled":
                    if service.binary == "nova-compute" and service.disabled_reason:
                        novaservice.append({"node-name": host,"status": "up", "datatype": "novaservice"})

                    novaservice.append({"node-name": host,"status": "down", "datatype": "novaservice"})
                elif service.state == "down":
                    novaservice.append({"node-name": host,"status": "down", "datatype": "novaservice"})
                else:
                    logger.error("nova compute on host %s is in an unknown State" % (service.host))
                counter+=1

                for i in novaservice:
                    status = i["status"]
                logger.info("nova-compute service in %s is %s" % (host, status))
            return novaservice

def get_service_status():
    nova_status = []
    n_c = NovaCompute()
    n_s = NovaService()

    for i in n_c.service_status():
        nova_status.append(i)

    for n in n_s.service_check():
        nova_status.append(n)

    return nova_status

