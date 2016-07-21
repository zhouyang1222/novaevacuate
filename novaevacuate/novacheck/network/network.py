import commands
import consul
import socket
import fcntl
import struct
import time
from netaddr import IPNetwork, IPAddress
from novaevacuate.log import logger
from novaevacuate.fence_agent import Fence
from novaevacuate.send_email import Email

class Network(object):
    def __init__(self):
        self.mgmt_ip = self.get_ip_address('br-mgmt')
        self.storage_ip = self.get_ip_address('br-storage')
        self.mgmt_consul = consul.Consul(host=self.mgmt_ip,port=8500)
        self.storage_consul = consul.Consul(host=self.storage_ip,port=8500)
        self.dict_networks = []
        (m, self.IPNetwork_m) = commands.getstatusoutput("LANG=C ip a show br-mgmt | awk '/inet /{ print $2 }'")
        (s, self.IPNetwork_s) = commands.getstatusoutput("LANG=C ip a show br-storage | awk '/inet /{ print $2 }'")
    
    def get_ip_address(self,ifname):
        """ 
        get local ip addr
        """

        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915, # SIOCGIFADDR
                struct.pack('256s',ifname[:15])
                )[20:24])
    
    def network_confirm(self,which_node,net):
        """
        retry three times to confirm the network,
        if confirm the network had died return true ,else return false
        """

        time.sleep(10)
        flag = 0
        while flag < 3:
            t_members = net.agent.members()
            for t_member in t_members:
                if t_member['Name'] == which_node and t_member['Status'] != 1:
                    time.sleep(10)
                elif t_member['Name'] == which_node and t_member['Status'] == 1:
                    return True
            flag = flag + 1
        return False

    def server_network_status(self,network):
        """
        Traversal all networks , when someone error , 
        assignment to dict and append to list
        """
        
        dict_network = {}
        members = network.agent.members()
        for member in members:
            if member['Status'] != 1:
                # when searched one network error , sleep awhile ,if it can restore auto
                if self.network_confirm(member['Name'],network):
                    continue                
                name = member['Name'].split('_')
                dict_network['name'] = name[1]
                dict_network['status'] = u'false'
                dict_network['addr'] = member['Addr']
                dict_network['role'] = member['Tags']['role']
                if IPAddress(member['Addr']) in IPNetwork(self.IPNetwork_m):
                    dict_network['net_role'] = 'br-mgmt'
                elif IPAddress(member['Addr']) in IPNetwork(self.IPNetwork_s):
                    dict_network['net_role'] = u'br-storage'
                # append the dict of error-network
                self.dict_networks.append(dict_network)
            elif member['Tags']['role'] == 'node':
                if IPAddress(member['Addr']) in IPNetwork(self.IPNetwork_m):
                    net_role = 'br-mgmt'
                elif IPAddress(member['Addr']) in IPNetwork(self.IPNetwork_s):
                    net_role = 'br-storage'
                logger.info("%s network %s is up" % (member['Name'],net_role))

def network_retry(node, name):
    """
    try to restore the network ,if no carried out fence
    """

    role = "network"
    if name == 'br-storage':
        commands.getstatusoutput("ssh %s ifdown %s" % (node,name))
        time.sleep(2)
        commands.getstatusoutput("ssh %s ifup %s" % (node,name))
        logger.info("ssh %s ifup %s" % (node,name))
        check_networks = get_net_status()
        # todo: node_check(node,name)
        if not check_networks:
            logger.info("%s %s recovery Success" % (node, name))
        else:
            for check_net in check_networks:
                if check_net['name'] == node and check_net['net_role'] == name:
                    logger.error("%s %s recovery failed."
                                 "Begin execute nova-compute service disable" % (node, name))
                    fence = Fence()
                    fence.compute_fence(role, node)
    else:
        message = "%s network %s had been error " % (node, name)
        email = Email()
        email.send_email(message)
        logger.info("send email with %s network %s had been error" % (node, name))

def get_net_status():
    """
    :return: list of error network
    """

    network_obj = Network()
    logger.info("start network check")
    network_obj.server_network_status(network_obj.mgmt_consul)
    network_obj.server_network_status(network_obj.storage_consul)
    return network_obj.dict_networks

# return current  leader
def leader():
    """
    return current  leader
    """

    network_obj = Network()
    storage_consul = network_obj.storage_consul
    try:
        if storage_consul.status.leader() == (network_obj.storage_ip + ":8300"):
            return "true"
        else:
            return "false"
    except Exception:
        logger.info("can't get consul leader")
        pass
