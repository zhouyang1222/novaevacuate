from novaevacuate.log import logger
import commands
from novaevacuate.openstack_novaclient import NovaClientObj as nova_client

class Net(object):

    def __init__(self):
        self._compute = nova_client.get_compute()[1]

    def icmp(self):
        for i in self._compute:
            s, result = commands.getstatusoutput("ping '%s'" % i)
            if s == 0 and result != None:
                return True


    def telnet(self):
        pass



