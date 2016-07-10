from credentials import get_nova_credentials_v2
from novaclient.client import Client as nova_Client
import re

class NovaClient(object):
    def __init__(self):
        self.nova_credentials = get_nova_credentials_v2()
        self.novaclient = nova_Client(**self.nova_credentials)
    
    def nova_evacuate(self,instance_host,on_shared_storage=True,password=None):
        """evacuate an instance
	return:
	   an instance of metadata
	"""
        return self.novaclient.servers.evacuate(instance_host,on_shared_storage,password)

    def nova_list(self,node_host):
        """list all instances of wrong compute-node
        return:
	   all instancs in wrong compute-node
	"""
	search_opts = {}
	search_opts['host'] = node_host
        instance_list = self.novaclient.servers.list(search_opts = search_opts)
	instances = []
	for instance in instance_list:
	    instances.append(re.search('(?<=<Server: ).*(?=>)',str(instance)).group(0))
	return instances

    def nova_service_list(self,node_host,binary="nova-compute"):
        """list one nova service of one node you want 
        default:
	   nova-compute
	return (service status and state)
	"""
        nova_compute = self.novaclient.services.list(host = node_host,binary = binary)
        return nova_compute[0].status,nova_compute[0].state

NovaClientObj = NovaClient()
if __name__ == "__main__":
        print NovaClientObj.nova_list("node-14.eayun.com")
        print NovaClientObj.nova_service_list("node-14.eayun.com")
