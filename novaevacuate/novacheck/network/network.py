import commands
import consul
import socket
import fcntl
import struct
import time
from novaevacuate.log import logger
from novaevacuate.fence_agent import Fence

# get local ip addr
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

"""
 retry three times to confirm the network, 
 if confirm the network had died ，return true ,else return false
"""
def network_confirm(which_node,net):
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

# Traversal all networks , when someone error , assignment to dict and append to list
def server_network_status(network,dict_network,dict_networks):
    members = network.agent.members()
    for member in members:
        mgmt = mgmt_ip.split('.')
        storage = storage_ip.split('.')
        ip_addr = member['Addr'].split('.')
        if member['Status'] != 1:
            # when searched one network error , sleep awhile ,if it can restore auto 
            if network_confirm(member['Name'],network):
                continue                
            name = member['Name'].split('_')
            dict_network['name'] = name[1]
            dict_network['status'] = u'false'
            dict_network['addr'] = member['Addr']
            dict_network['role'] = member['Tags']['role']
            if mgmt[0]==ip_addr[0] and mgmt[1]==ip_addr[1] and mgmt[2]==ip_addr[2]:
                dict_network['net_role'] = 'br-mgmt'
            elif storage[0]==ip_addr[0] and storage[1]==ip_addr[1] and storage[2]==ip_addr[2]:
                dict_network['net_role'] = u'br-storage'
            # append the dict of error-network   
            dict_networks.append(dict_network)
        elif member['Tags']['role'] == 'node':
            if mgmt[0]==ip_addr[0] and mgmt[1]==ip_addr[1] and mgmt[2]==ip_addr[2]:
                net_role = 'br-mgmt'
            elif storage[0]==ip_addr[0] and storage[1]==ip_addr[1] and storage[2]==ip_addr[2]:
                net_role = 'br-storage'
            logger.info("%s network %s is up" % (member['Name'],net_role))
# transfer this function ，return  list of error network
def get_net_status():
    logger.info("start network check")
    dict_network = {'name': 'null', 'status': 'true', 'addr': 'null', 'role': 'null', 'net_role': 'null'}
    dict_networks = []
    server_network_status(mgmt_consul,dict_network,dict_networks)
    server_network_status(storage_consul,dict_network,dict_networks)
    return dict_networks
# return current  leader
def leader():
    try:
        if storage_consul.status.leader() == (get_ip_address('br-storage') + ":8300"):
            return "true"
        else:
            return "false"
    except Exception:
        pass
# try to restore the network ,if no carried out fence
def network_retry(node, name):
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
        logger.info("send email to ...")
# init data
mgmt_ip = get_ip_address('br-mgmt')
storage_ip = get_ip_address('br-storage')
mgmt_consul = consul.Consul(host=mgmt_ip,port=8500)
storage_consul = consul.Consul(host=storage_ip,port=8500)
