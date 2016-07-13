import consul
import socket
import fcntl
import struct
import time
from novaevacuate.log import logger


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def server_network_status(network,dict_network,dict_networks):
    # print 'leader :',network.status.leader()
    members = network.agent.members()
    for member in members:
        mgmt = mgmt_ip.split('.')
        storage = storage_ip.split('.')
        ip_addr = member['Addr'].split('.')
        # print member['Status'],member['Name'],member['Addr'],member['Tags']['role']
        if member['Status'] != 1:
            # print "the node faild"
            name = member['Name'].split('_')
            dict_network['name'] = name[1]
            dict_network['status'] = u'false'
            dict_network['addr'] = member['Addr']
            dict_network['role'] = member['Tags']['role']
            #mgmt = mgmt_ip.split('.')
            #storage = storage_ip.split('.')
            #ip_addr = member['Addr'].split('.')
            if mgmt[0]==ip_addr[0] and mgmt[1]==ip_addr[1] and mgmt[2]==ip_addr[2]:
                dict_network['net_role'] = 'br-mgmt'
            elif storage[0]==ip_addr[0] and storage[1]==ip_addr[1] and storage[2]==ip_addr[2]:
                dict_network['net_role'] = u'br-storage'
            print dict_network
            dict_networks.append(dict_network)
        elif member['Tags']['role'] == 'node':
            if mgmt[0]==ip_addr[0] and mgmt[1]==ip_addr[1] and mgmt[2]==ip_addr[2]:
                net_role = 'br-mgmt'
            elif storage[0]==ip_addr[0] and storage[1]==ip_addr[1] and storage[2]==ip_addr[2]:
                net_role = 'br-storage'
            logger.info("%s network %s is up" % (member['Name'],net_role))

def try_connected(network_consul,network_ip):
    while network_consul:
        try:
            network_consul.agent.self()
            break
        except Exception:
            network_consul = consul.Consul(host=network_ip,port=8500)
            # print ".........."
            pass
def get_net_status():
    logger.info("start network check")
    dict_network = {'name': 'null', 'status': 'true', 'addr': 'null', 'role': 'null', 'net_role': 'null'}
    dict_networks = []
    try_connected(mgmt_consul,mgmt_ip)
    try_connected(storage_consul,mgmt_consul)
    server_network_status(mgmt_consul,dict_network,dict_networks)
    server_network_status(storage_consul,dict_network,dict_networks)
    return dict_networks

def leader():
    if storage_consul.status.leader() == (get_ip_address('br-storage') + ":8300"):
        return "true"
    else:
        return "false"

mgmt_ip = get_ip_address('br-mgmt')
storage_ip = get_ip_address('br-storage')
mgmt_consul = consul.Consul(host=mgmt_ip,port=8500)
storage_consul = consul.Consul(host=storage_ip,port=8500)
