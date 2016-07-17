from novacheck.network.network import get_net_status as network_check
from novacheck.service.service import get_service_status as service_check
from novaevacuate.novacheck.service.service import NovaService
from novaevacuate.novacheck.service.service import NovaCompute
from novaevacuate.log import logger
import time

COUNT = 3
class FenceAgent(object):
    def _check(self,role,node,name):
        wrong_item = []
        if role == 'network':
            wrong_list = network_check()
        elif role == 'service':
            service_list = service_check()
            for service in service_list:
                if service['status'] == False:
                        wrong_item.append(service)
        if wrong_list:
            return True
        else:
            return False


    def recovery(self, role, node, name):
        counter = 1
        check_bool = self._check(role, node, name)
        while counter <= COUNT:
            check_bool = self._check(role, node, name)
            if check_bool:
                if role == "network":
                    logger.warn("%s %s has wrong,Begin try the  %d check" %
                                (node, name, counter))
                elif role == "service":
                    logger.warn("%s %s has wrong,Begin try the  %d check" %
                                (node, name, counter))

            else:
                # new_check_bool = False
                logger.info("%s %s is auto recovery" % (node, name))
                break
            counter += 1
            time.sleep(10)
            continue
        if check_bool:
            NovaService.service_fence(node)

        """
        for i in range(COUNT):
            # service_name = "openstack-nova-compute"
            if check_bool:
                if role == "network":
                    logger.warn("%s %s has wrong,Begin try the  %d check" %
                                (node, name, i))
                    pass
                elif role == "service":
                    logger.warn("%s %s has wrong,Begin try the  %d check" %
                                (node, name, i))
                    # NovaService.service_recovery(node, name)
            else:
                new_check_bool = False
                logger.info("%s %s is recovery" % (node, name))

            time.sleep(10)
            self._check(role, node, name)

        if check_bool:
            NovaService.service_fence()
        """

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


FenceCheck = FenceAgent()
