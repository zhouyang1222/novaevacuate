# fence agent have three fence status
# 1. Power fencing
# 2. Fencing from storage in Cinder
# 3. Fencing from network in Neutron
# 4. Self fencing by Nova Compute

import datetime
from openstack_novaclient import NovaClientObj as nova_client
import commands
from novaevacuate.novacheck.network.network import get_net_status as network_check
from novaevacuate.novacheck.service.service import get_service_status as service_check
from novaevacuate.log import logger
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
	        wrong_list = service_check()
	    if wrong_list:
	        for wrong_element in wrong_list:
	            if node in wrong_element and name in wrong_element:
		        continue
		        #wrong_item.append((node,name))
		    else:
		        return False
	    else:
	        return False
	#if wrong_item and (wrong_item[0] == wrong_item[1]):
	#    return True
	#else:
	#    return False
	return True
    def _recovery(self,role,node,name):
        cmd = {'service':'systemctl restart %s' % name,
	       'network':'ifdown %s && ifup %s' % (name,name)}
        check_bool = self._check(role,node,name)
        if check_bool:
	    (status,info) = commands.getstatusoutput("ssh %s %s" % (node,cmd[role]) )
	    if status == 0:
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
            self.fence(node)
	    self.instance_evacuate(node)
    def service_recovery(self, node, name):
        check_result = self._recovery('service',node,name)
	#todo: service_check(node,name)
        if not check_result:
	    logger.info("%s %s recovery Success" % (node,name)
	else:
	    #先fence
	    self.fence(node)
	    #再迁移
	    self.instance_evacuate(node)
    def fence(self,node):
        nova_client.nova_service_disable(node)        
    def instance_evacuate(self, node):
        #先获取异常计算节点的所有云主机的名称
        instances = nova_client.nova_list(node)
	#再循环将云主机迁移
	for instance in instances:
            nova_client.nova_evacuate(instance)
FenceCheck = FenceAgent()
