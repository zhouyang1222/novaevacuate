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
from novaevacuate.novacheck.service.service import NovaService
from novaevacuate.novacheck.service.service import NovaCompute
from novaevacuate.log import logger
import time

NS = NovaService()
NC = NovaCompute()

COUNT = 3
class FenceAgent(object):
    def _check(self,role,node,name):
        wrong_item = []
        for i in range(COUNT):
            time.sleep(10)
            if role == 'network':
                logger.warn("%s %s has wrong,Begin try the %d network check" % (node, name, i))
                wrong_list = network_check()
            elif role == 'service':
                logger.warn("%s %s has wrong,Begin try the %d network check" % (node, name, i))
                wrong_list = []
                service_list = service_check()
                for service in service_list:
                    if service['status'] == "down":
                        wrong_list.append(service)   
            if wrong_list:
                for wrong_element in wrong_list:
                    if node in str(wrong_element) and name in str(wrong_element):
                        continue
                    # wrong_item.append((node,name))
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
        # todo: node_check(node,name)
        if not check_result:
            logger.info("%s %s recovery Success" % (node, name))
        else:
            logger.error("%s %s recovery failed."
                         "Begin execute nova-compute service disable")
            NS.service_fence(node)
            NC.nova_stop(node)

            self.instance_evacuate(node)

    def service_recovery(self, node, name):
        check_result = self._recovery('service',node, name)
        # todo: service_check(node,name)
        if not check_result:
            logger.info("%s %s recovery Success" % (node, name))
        else:
            logger.warn("%s Nova service failed."
                        "Begin execute nova-compute service disable" % node)
            NS.service_fence(node)
            # logger.info("start evacuate")
            # self.instance_evacuate(node)

    #def fence(self,node):
    #    nova_client.nova_service_disable(node)
    #    logger.warn("%s nova-compute service is disabled."
    #                "Nova cloud not create instance in %s" % (node, node))

    def instance_evacuate(self, node):
        instances = nova_client.nova_list(node)
        try:
            for instance in instances:
                logger.warn("%s server start evacuate" % instance)
                nova_client.nova_evacuate(instance)
        except Exception as e:
            logger.error(e)

FenceCheck = FenceAgent()
