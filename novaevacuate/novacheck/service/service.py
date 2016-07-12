import sys
import re
import commands
import novaclient
from novaclient import client
from novaevacuate.credentials import get_nova_credentials_v2
from novaevacuate.log import logger

HOST = "compute"
BINARY = "nova-compute"

#program exit stat define
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


#host status define
HOST_DEAD='dead'
HOST_ACTIVE='running'
HOST_FAILD='faild'
HOST_FENCE='FENCE'

#nova compute services status define
service_status = "enable"
service_state = "up"

def get_compute():
    creds = get_nova_credentials_v2()
    nova = client.Client(**creds)
    try:
        services = nova.services.list(binary="nova-compute")
    except novaclient.exceptions.Unauthorized:
        print("Failed to authenticate to Keystone")
        sys.exit(-1)
    except Exception:
        print("Failed to query service")
        sys.exit(-1)

    node_count = len(services)
    counter = 0
    node_name = []

    while counter < node_count:
        service = services[counter]
        node_name.append(service.host)
        counter+=1

    return service, node_name

class NovaCompute():
    def __init__(self):
        self.compute = get_compute()[1]

    def service_status(self):
        # status is list example: [{'status': 'up', 'node-name': 'node1', 'type': 'nova-compute'},
        # {'status': 'down', 'node-name': 'node-2', 'type': 'nova-compute'}]

        novacompute = []
        for i in self.compute:
            (s, o) = commands.getstatusoutput("ssh '%s' systemctl -a|grep openstack-nova-compute" % (i))
            if s == 0 and o != None:
                service_status = o

            if re.search('runing', service_status) and re.search('active', service_status):
                novacompute.append[{"node-name": i,"status": "active", "datatype": "novacompute"}]
            elif re.search('dead', service_status) and re.search('inactive', service_status):
                novacompute.append[{"node-name": i,"status": "dead", "datatype": "novacompute"}]
            elif re.search('faild', service_status):
                novacompute.append[{"node-name": i,"status": "faild", "datatype": "novacompute"}]

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
        self.creds = get_nova_credentials_v2()
        self.nova = client.Client(**self.creds)
        self.service = get_compute()[0]
        # self.compute = get_compute()[1]

    def service_check(self):
        novaservice = []
        services = self.service_status()[0]

        if not services:
            logger.warn("Service could not be found nova-compute")
            sys.exit(UNKNOWN)
        else:
            counter = 0
            count = len(services)
            while counter < count:
                service = services[counter]
                if service.status == "enable" and service.state == "up":
                    novaservice.append[{"node-name": service.host,"status": service.state, "datatype": "novaservice"}]
                    # print ("nova compute service on host %s is OK " % (HOST))
                    sys.exit(OK)
                elif service.status == "disabled":
                    if service.binary == "nova-compute" and service.disabled_reason:
                        service.state = "up"
                        novaservice.append[{"node-name": service.host,"status": service.state, "datatype": "novaservice"}]
                        # print ("nova compute service on host %s is Reserved" %
                        #       (HOST))
                        sys.exit(OK)

                    novaservice.append[{"node-name": service.host,"status": service.state, "datatype": "novaservice"}]
                    # print ("nova compute service on host %s is Disabled" %
                    #       (HOST))
                    sys.exit(WARNING)
                elif service.state == "down":
                    novaservice.append[{"node-name": service.host,"status": service.state, "datatype": "novaservice"}]
                    # print ("nova compute service on host %s is Down" %
                    #       (HOST))
                    sys.exit(CRITICAL)
                else:
                    logger.error("nova compute on host %s is in an unknown State" % (service.host))
                    # print ("nova compute on host %s is in an unknown State" %
                    #       (HOST))
                    sys.exit(UNKNOWN)
                counter+=1
            return novaservice

def get_service_status():
    nova_status = []
    n_c = NovaCompute.service_status()
    n_s = NovaService.service_check()

    for i in n_c:
        nova_status.append(i)

    for n in n_s:
        nova_status.append(n)

    return nova_status



