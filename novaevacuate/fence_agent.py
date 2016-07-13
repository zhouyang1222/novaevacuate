# fence agent have three fence status
# 1. Power fencing
# 2. Fencing from storage in Cinder
# 3. Fencing from network in Neutron
# 4. Self fencing by Nova Compute

import datetime
from openstack_novaclient import NovaClientObj as nova_client
import commands
from novacheck.network.network import get_net_status as network_check
from novacheck.service.service import get_service_status as service_check
from log import logger
import time

COUNT=3
class FenceAgent(object):
    def _check(self,role,node,name):
        wrong_item = []
        for i in range(COUNT):
            time.sleep(60)
            if role == 'network':
                wrong_list = network_check()
            elif role == 'service':
                wrong_list = []
                service_list = service_check()
                for service in service_list:
                    if service['status'] == "down":
                        wrong_list.append(service)   
            if wrong_list:
                for wrong_element in wrong_list:
                    if node in str(wrong_element) and name in str(wrong_element):
                        continue
                    #wrong_item.append((node,name))
                    else:
                        return False
            else:
                return False
        # if wrong_item and (wrong_item[0] == wrong_item[1]):
        # return True
        # else:
        # return False
        return True
    def _recovery(self,role,node,name):
        service_name = "openstack-nova-compute"
        cmd = {'service':['ssh %s systemctl restart %s' % (node,service_name)],
               'network':['ssh %s ifdown %s' % (node,name),
                          'ssh %s ifup %s' % (node,name)]}
        check_bool = self._check(role,node,name)
        if check_bool:
            for cmd_line in cmd[role]:
                (status,info) = commands.getstatusoutput(cmd_line)
                if status:
                    logger.error(info)
            new_check_bool = self._check(role,node,name)
        else:
            new_check_bool = False
        return new_check_bool

    def network_recovery(self, node, name):
        check_result = self._recovery('network',node,name)
        #todo: node_check(node,name)
        if not check_result:
            logger.info("%s %s recovery Success" % (node, name))
        else:
            logger.info("start fence")
            self.fence(node)
            (status,info) = commands.getstatusoutput("ssh %s systemctl stop openstack-nova-compute" % node)
            logger.info(info)
            logger.info("start evacuate")
            self.instance_evacuate(node)
    def service_recovery(self, node, name):
        check_result = self._recovery('service',node,name)
        # todo: service_check(node,name)
        if not check_result:
            logger.info("%s %s recovery Success" % (node,name))
        else:
            logger.info("start fence")
            self.fence(node)
            logger.info("start evacuate")
            self.instance_evacuate(node)
    def fence(self,node):
        nova_client.nova_service_disable(node)        
    def instance_evacuate(self, node):
        instances = nova_client.nova_list(node)
        for instance in instances:
            nova_client.nova_evacuate(instance)
FenceCheck = FenceAgent()
