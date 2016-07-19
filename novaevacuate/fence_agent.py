import time
import commands
from novaevacuate.log import logger
from novaevacuate.openstack_novaclient import NovaClientObj as nova_client
from novaevacuate.evacuate_vm_action import EvacuateVmAction

FENCE_NODES = []


class Fence(object):

    def compute_fence(self, role, node):
        nova_client.nova_service_disable(node)
        commands.getoutput("ssh '%s' systemctl stop openstack-nova-compute" % node)

        logger.warn("%s nova-compute service is disabled."
                    "Nova cloud not create instance in %s" % (node, node))

        # add Fence node to global FENCE_NODES list
        if node in FENCE_NODES:
            logger.info("%s has been fence status" % node)
        else:
            FENCE_NODES.append(node)

            if role == "network":
                flag = 0
                while True:
                    service_status = nova_client.service_status()
                    time.sleep(10)
                    if service_status:
                        for i in service_status:
                            if node == i["node-name"]:
                                if i["status"] == "disabled" and i["state"] == "down":
                                    # when execut vm_evacuate , must exec nova service
                                    # check get nova service
                                    # status and state
                                    logger.warn("%s has error, the instance will evacuate" % node)
                                    self.vm_evacuate(node)
                                    flag = 1
                    if flag == 0:
                        continue
                    else:
                        break

    def compute_fence_recovery(self, node, name):
        # when the node reboot must enable nova-compute enable
        nova_client.nova_service_enable(node)
        logger.info("%s nova-compute service is enabled.")

    def vm_evacuate(self, node):
        nova_evacuate = EvacuateVmAction(node)
        nova_evacuate.run()

