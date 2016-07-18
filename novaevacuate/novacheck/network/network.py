import commands
import consul
import socket
import fcntl
import struct
import time
from novaevacuate.log import logger
#from novaevacuate.evacuate_vm_action import EvacuateVmAction
from novaevacuate.novacheck.service.service import NovaService

COUNT = 3

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def server_network_status(network,dict_network,dict_networks):
    members = network.agent.members()
    for member in members:
        if member['Status'] != 1:
            name = member['Name'].split('_')
            dict_network['name'] = name[1]
            dict_network['status'] = u'false'
            dict_network['addr'] = member['Addr']
            dict_network['role'] = member['Tags']['role']
            mgmt = mgmt_ip.split('.')
            storage = storage_ip.split('.')
            ip_addr = member['Addr'].split('.')
            if mgmt[0]==ip_addr[0] and mgmt[1]==ip_addr[1] and mgmt[2]==ip_addr[2]:
                dict_network['net_role'] = 'br-mgmt'
            elif storage[0]==ip_addr[0] and storage[1]==ip_addr[1] and storage[2]==ip_addr[2]:
                dict_network['net_role'] = u'br-storage'
            dict_networks.append(dict_network)

def try_connected(network_consul,network_ip):
    while network_consul:
        try:
            network_consul.agent.self()
            break
        except Exception:
            network_consul = consul.Consul(host=network_ip,port=8500)
            pass

def network_confirm(which_node):
    time.sleep(10)
    t_members = network.agent.members()
    flag = 0
    while(1):
        t_members = network.agent.members()
        if t_members[which_node]['Status'] != 1:
            if flag == 3:
                break
            else:
                time.sleep(10)
        else:
            return True
        flag = flag + 1
    return False

def server_network_status(network,dict_network,dict_networks):
    members = network.agent.members()
    flag_mem = 0
    for member in members:
        mgmt = mgmt_ip.split('.')
        storage = storage_ip.split('.')
        ip_addr = member['Addr'].split('.')
        if member['Status'] != 1:
            if network_confirm(flag_mem):
               continue                
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
            dict_networks.append(dict_network)
        elif member['Tags']['role'] == 'node':
            if mgmt[0]==ip_addr[0] and mgmt[1]==ip_addr[1] and mgmt[2]==ip_addr[2]:
                net_role = 'br-mgmt'
            elif storage[0]==ip_addr[0] and storage[1]==ip_addr[1] and storage[2]==ip_addr[2]:
                net_role = 'br-storage'
            logger.info("%s network %s is up" % (member['Name'],net_role))
        flag = flag + 1

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


def recovery(node, name):
    counter = 1
    while counter <= COUNT:
        check_bool = get_net_status()
        if check_bool:
            logger.warn("%s %s has wrong,Begin try the  %d check" %
                            (node, name, counter))
        else:
            # new_check_bool = False
            logger.info("%s %s is auto recovery" % (node, name))
            break
        counter += 1
        time.sleep(10)
        continue
    check_bool = get_net_status()
    if check_bool:
        commands.getstatusoutput("ssh %s ifdown %s" % (node,name))
        time.sleep(2)
        commands.getstatusoutput("ssh %s ifup %s" % (node,name))

def network_recovery(node, name):
    check_result = recovery(node,name)
    # todo: node_check(node,name)
    if not check_result:
        logger.info("%s %s recovery Success" % (node, name))
    else:
        logger.error("%s %s recovery failed."
                     "Begin execute nova-compute service disable")
        NovaService.service_fence(node)
#        NS.service_fence(node)
#        NC.nova_stop(node)
#        nova_evacuate = EvacuateVmAction(node)
#        nova_evacuate.run()


mgmt_ip = get_ip_address('br-mgmt')
storage_ip = get_ip_address('br-storage')
mgmt_consul = consul.Consul(host=mgmt_ip,port=8500)
storage_consul = consul.Consul(host=storage_ip,port=8500)
