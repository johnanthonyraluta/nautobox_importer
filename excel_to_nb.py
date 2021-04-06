import argparse,json,requests
from pathlib import Path
import collections
from pprint import pprint
import pynautobot
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
error_log = open("errors_excel_to_nb.log", "w")


import sys
sys.path.append("libs")
from libs.xlsx_handler import xlsx_handler
from libs.data_collector import xlsx_graph

file = open('nautobox.json', 'r')
account = json.load(file)
NB_URL= account['NB_URL']
TOKEN= account['TOKEN']
file.close()

nb = pynautobot.api(
    url=NB_URL,
    token=TOKEN,
)

nb.http_session.verify = False

def hostname2code(hostname):
    if "CICU" in hostname:
        device_type="AN"
    elif "CICN" in hostname:
        device_type="DN"
    elif "CIRO" in hostname:
        device_type="ASBR"
    elif "CIBP" in hostname:
        device_type="P"
    elif "CIBE" in hostname:
        device_type="PE"
    else:
        device_type= None
    return device_type

def device2code(device_type):
    if "AN-" in device_type:
        _hardware="NCS5504"
        _role="AN"
    elif "DN-" in device_type:
        _hardware="NCS5508"
        _role="DN"

    elif "ASBR-" in device_type:
        _hardware="ASR9910"
        _role="ASBR"

    elif "P-" in device_type:
        _hardware="NCS5508"
        _role="P"

    elif "PE-" in device_type:
        _hardware="ASR9910"
        _role="PE"
    elif "T-RR" in device_type:
        _hardware="Virtual Router"
        _role="T-RR"
    elif "S-RR" in device_type:
        _hardware="Virtual Router"
        _role="S-RR"
    elif "XTC" in device_type:
        _hardware="Virtual Router"
        _role="XTC"
    else:
        _hardware= None
        _role=None

    return _role,_hardware

def clean(txt):
    if txt==None:
        return None
    if type(txt) == str:
        return txt.strip()
    if type(txt) == int:
        return str(txt).strip()

def load_data(filename,nodesheet):
    xl=xlsx_handler(filename)
    data=xl.read_all(nodesheet)
    emp={}
    all_row=[]
    for i in data:
        tmp=emp.copy()
        if i["hostname"] != None:
            tmp["site_name"]=clean(i["site_name"])
            tmp["device_type"]=clean(i["device_type"])
            tmp["hostname"]=clean(i["hostname"])
            tmp["region"]=clean(i["region"])
            tmp["ipv4_loopback0"]=clean(i["ipv4_loopback0_address"])
            tmp["ipv4_loopback1"]=clean(i["ipv4_management_ip"])
            tmp["ipv6_loopback0"]=clean(i["ipv6_loopback0_address"])
            tmp["ipv6_loopback1"]=clean(i["ipv6_management_ip"])
            tmp["ipv4_anycast"]=clean(i["ipv4_anycast_ip"])
            tmp['sid_absolute_prefix']=clean(i["sid_asolute_prefix"])
            tmp['sid_absolute_strict_prefix']=clean(i["sid_absolute_strict_prefix"])
            tmp['any_cast_sid']=clean(i["any_cast_sid"])
            tmp['phase']=clean(i["phase 1"])
            all_row.append(tmp)
    return all_row

def api_node(node_data):
    site=[]
    device_list=[]
    for x in node_data:
        if x['site_name'] != None and x['region'] != None:
            site.append({"name": x['site_name'].replace('.',''),
                        "region": {'name': x['region'], 'slug': x['region'].lower()},
                        'slug':x['site_name'].lower().replace('-','').replace(' ','_').replace('.','').replace(',','').replace('(','').replace(')',''),
                        'tenant': {'name': 'PLDT', 'slug': 'pldt'},
                        'status': 'active'
                        })
        if x['device_type'] != None:
            temp={
                'name': x['hostname'],
                'device_type': {
                    'model':device2code(x['device_type'])[1],
                    'slug':device2code(x['device_type'])[1].lower().replace(' ','_')},
                'device_role': {
                    'name':device2code(x['device_type'])[0],
                    'slug':device2code(x['device_type'])[0].lower().replace(' ','_')
                },
                'site': {
                    "name": x['site_name'].replace('.',''),
                    'slug':x['site_name'].lower().replace('-','').replace(' ','_').replace('.','').replace(',','').replace('(','').replace(')','')
                },
                'platform': {'name':'IOS-XR','slug':'ios-xr'},
                'tenant': {'name':'PLDT','slug':'pldt'},
                'status': 'active'
            }
            device_list.append(temp)

    return site,device_list


def add_device(device_list):
    for x in device_list:
        try:
            nb.dcim.devices.create(x)
        except pynautobot.RequestError as e:
            error_log.write("{0}\n{1}\n".format(x['name'], str(e.error)))
            print(x['name'])
            print(e.error)
            pass

def add_site(site_list):
    for x in site_list:
        try:
            nb.dcim.sites.create(x)
        except pynautobot.RequestError as e:
            error_log.write("{0}\n{1}\n".format(x['name'], str(e.error)))
            print(x['name'])
            print(e.error)
            pass

def add_loopback():
    for i in p.nodes:
        data=p.nodes[i]
        temp_loop0={
                'device': {'name': data['hostname']},
                'name': 'Loopback0',
                'type': 'virtual'
            }
        temp_loop1={
                'device': {'name': data['hostname']},
                'name': 'Loopback1',
                'type': 'virtual',
                'mgmt_only': True
            }
        temp_any={
                'device': {'name': data['hostname']},
                'name': 'Loopback100',
                'type': 'virtual'
            }
        try:
            nb.dcim.interfaces.create(temp_loop0)
        except pynautobot.RequestError as e:
            error_log.write("{0} {1}\n{2}\n".format(temp_loop0['device']['name'],temp_loop0['name'], str(e.error)))
            print(temp_loop0['device']['name'],temp_loop0['name'])
            print(e.error)
            pass
        try:
            nb.dcim.interfaces.create(temp_loop1)
        except pynautobot.RequestError as e:
            error_log.write("{0} {1}\n{2}\n".format(temp_loop1['device']['name'],temp_loop1['name'], str(e.error)))
            print(temp_loop1['device']['name'],temp_loop1['name'])
            print(e.error)
            pass
        try:
            if data['ipv4_loopback100'] != None:
                nb.dcim.interfaces.create(temp_any)
        except pynautobot.RequestError as e:
            error_log.write("{0} {1}\n{2}\n".format(temp_any['device']['name'],temp_any['name'], str(e.error)))
            print(temp_loop1['device']['name'],temp_any['name'])
            print(e.error)
            pass

def add_bundle_interface():
    for i in p.nodes:
        data=p.nodes[i]
        for x in data['bundles']:
            temp_dict={
                'device': {'name': x['source_hostname']},
                'name': x['source_bundle_interface'],
                'type': 'lag'
            }
            try:
                nb.dcim.interfaces.create(temp_dict)
            except pynautobot.RequestError as e:
                error_log.write("{0} {1}\n{2}\n".format(temp_dict['device']['name'],temp_dict['name'], str(e.error)))
                print(temp_dict['device']['name'],temp_dict['name'])
                print(e.error)
                pass

def add_phy_interface():
    for i in p.nodes:
        data=p.nodes[i]
        for x in data['interfaces']:
            temp_dict={
                'device': {'name': x['source_hostname']},
                'name': x['source_interface_id'],
                'type': '100gbase-x-qsfp28',
                'lag': {'name': x['source_bundle_interface'], 'device': {'name': x['source_hostname']}}
            }
            try:
                nb.dcim.interfaces.create(temp_dict)
            except pynautobot.RequestError as e:
                error_log.write("{0} {1}\n{2}\n".format(temp_dict['device']['name'],temp_dict['name'], str(e.error)))
                print(temp_dict['device']['name'],temp_dict['name'])
                print(e.error)
                pass
#
def add_connection():
    for i in p.nodes:
        data=p.nodes[i]
        for x in data['interfaces']:
            source = nb.dcim.interfaces.get(name=x['source_interface_id'],device=x['source_hostname'])
            target = nb.dcim.interfaces.get(name=x['target_interface_id'],device=x['target_hostname'])
            if source != None and target != None:
                try:
                    nb.dcim.cables.create(
                    {'termination_a_type': 'dcim.interface',
                    'termination_a_id': source.id,
                    'termination_b_type': 'dcim.interface',
                    'termination_b_id': target.id,
                    'status': 'connected'}
                    )
                except pynautobot.RequestError as e:
                    error_log.write("{0} {1}\n{2}\n".format(source,target, str(e.error)))
                    print(source,target)
                    print(e.error)
                    pass

def assign_ipv4():
    for i in p.nodes:
        data=p.nodes[i]
        for x in data['bundles']:
            if x['source_bundle_ipv4'] != None and x['target_bundle_ipv4'] != None:
                bundle=nb.dcim.interfaces.get(name=x['source_bundle_interface'],device=data['hostname'])
                dup_ip = nb.ipam.ip_addresses.get(assigned_object_id=bundle.id,address=x['source_bundle_ipv4'])
                if bundle != None and dup_ip == None:
                    temp_dict={
                    'address': x['source_bundle_ipv4'],
                    "status": "active",
                    "tenant": {'name': 'PLDT', 'slug': 'pldt'},
                    "assigned_object_type": "dcim.interface",
                    'assigned_object_id': bundle.id,
                    'assigned_object': {'id': bundle.id, 'device': {'name': data['hostname']}}
                    }
                    try:
                        nb.ipam.ip_addresses.create(temp_dict)
                    except pynautobot.RequestError as e:
                        error_log.write("{0} {1}\n{2}\n".format(data['hostname'],x['source_bundle_ipv4'], str(e.error)))
                        print(data['hostname'],x['source_bundle_ipv4'])
                        print(e.error)
                        pass
                if dup_ip != None:
                    error_log.write("{0} {1} already assigned\n".format(data['hostname'],x['source_bundle_ipv4']))
                    print(x['source_bundle_ipv4']+ " already assigned")

        if nb.dcim.interfaces.get(name='Loopback0',device=data['hostname']) != None:
            loopback0=nb.dcim.interfaces.get(name='Loopback0',device=data['hostname'])
            dup_ip = nb.ipam.ip_addresses.get(assigned_object_id=loopback0.id,address=data['ipv4_loopback0'])
            if loopback0 != None and dup_ip == None:
                temp_loop0={
                    'address': data['ipv4_loopback0'],
                    "status": "active",
                    "role": "loopback",
                    "tenant": {'name': 'PLDT', 'slug': 'pldt'},
                    "assigned_object_type": "dcim.interface",
                    'assigned_object_id': loopback0.id,
                    'assigned_object': {'id': loopback0.id, 'device': {'name': data['hostname']}}
                }
                try:
                    nb.ipam.ip_addresses.create(temp_loop0)
                except pynautobot.RequestError as e:
                    error_log.write("{0} {1}\n{2}\n".format(data['hostname'],x['ipv4_loopback0'], str(e.error)))
                    print(data['hostname'],x['ipv4_loopback0'])
                    print(e.error)
                    pass
            if dup_ip != None:
                error_log.write("{0} {1} already assigned\n".format(data['hostname'],x['ipv4_loopback0']))
                print(x['ipv4_loopback0']+ " already assigned")

        if nb.dcim.interfaces.get(name='Loopback1',device=data['hostname']) != None:
            loopback1=nb.dcim.interfaces.get(name='Loopback1',device=data['hostname'])
            dup_ip = nb.ipam.ip_addresses.get(assigned_object_id=loopback1.id,address=data['ipv4_loopback1'])
            if loopback1 != None and dup_ip == None:
                temp_loop1={
                    'address': data['ipv4_loopback1'],
                    "status": "active",
                    "role": "loopback",
                    "tenant": {'name': 'PLDT', 'slug': 'pldt'},
                    "assigned_object_type": "dcim.interface",
                    'assigned_object_id': loopback1.id,
                    'assigned_object': {'id': loopback1.id, 'device': {'name': data['hostname']}}
                }
                try:
                    nb.ipam.ip_addresses.create(temp_loop1)
                except pynautobot.RequestError as e:
                    error_log.write("{0} {1}\n{2}\n".format(data['hostname'],x['ipv4_loopback1'], str(e.error)))
                    print(data['hostname'],x['ipv4_loopback1'])
                    print(e.error)
                    pass

            if dup_ip != None:
                error_log.write("{0} {1} already assigned\n".format(data['hostname'],x['ipv4_loopback1']))
                print(x['ipv4_loopback1']+ " already assigned")

        if nb.dcim.interfaces.get(name='Loopback100',device=data['hostname']) != None:
            loopback100=nb.dcim.interfaces.get(name='Loopback100',device=data['hostname'])
            dup_ip = nb.ipam.ip_addresses.get(assigned_object_id=loopback100.id,address=data['ipv4_loopback100'])
            if loopback100 != None and dup_ip == None:
                temp_loop100={
                    'address': data['ipv4_loopback100'],
                    "status": "active",
                    "role": "anycast",
                    "tenant": {'name': 'PLDT', 'slug': 'pldt'},
                    "assigned_object_type": "dcim.interface",
                    'assigned_object_id': loopback100.id,
                    'assigned_object': {'id': loopback100.id, 'device': {'name': data['hostname']}}
                }
                try:
                    nb.ipam.ip_addresses.create(temp_loop100)
                except pynautobot.RequestError as e:
                    error_log.write("{0} {1}\n{2}\n".format(data['hostname'],x['ipv4_loopback100'], str(e.error)))
                    print(data['hostname'],x['ipv4_loopback100'])
                    print(e.error)
                    pass
            if dup_ip != None:
                error_log.write("{0} {1} already assigned\n".format(data['hostname'],x['ipv4_loopback100']))
                print(x['ipv4_loopback100']+ " already assigned")


def assign_ipv6():
    for i in p.nodes:
        data=p.nodes[i]
        for x in data['bundles']:
            if x['source_bundle_ipv6'] != None and x['target_bundle_ipv6'] != None:
                bundle=nb.dcim.interfaces.get(name=x['source_bundle_interface'],device=data['hostname'])
                dup_ip = nb.ipam.ip_addresses.get(assigned_object_id=bundle.id,address=x['source_bundle_ipv6'])
                if bundle != None and dup_ip == None:
                    temp_dict={
                    'address': x['source_bundle_ipv6'],
                    "status": "active",
                    "tenant": {'name': 'PLDT', 'slug': 'pldt'},
                    "assigned_object_type": "dcim.interface",
                    'assigned_object_id': bundle.id,
                    'assigned_object': {'id': bundle.id, 'device': {'name': data['hostname']}}
                    }
                    try:
                        nb.ipam.ip_addresses.create(temp_dict)
                    except pynautobot.RequestError as e:
                        error_log.write("{0} {1}\n{2}\n".format(data['hostname'],x['source_bundle_ipv6'], str(e.error)))
                        print(data['hostname'],x['source_bundle_ipv6'])
                        print(e.error)
                        pass
                if dup_ip != None:
                    error_log.write("{0} {1} already assigned\n".format(data['hostname'],x['source_bundle_ipv6']))
                    print(x['source_bundle_ipv6']+ " already assigned")

        if nb.dcim.interfaces.get(name='Loopback0',device=data['hostname']) != None:
            loopback0=nb.dcim.interfaces.get(name='Loopback0',device=data['hostname'])
            dup_ip = nb.ipam.ip_addresses.get(assigned_object_id=loopback0.id,address=data['ipv6_loopback0'])
            if loopback0 != None and dup_ip == None:
                temp_loop0={
                    'address': data['ipv6_loopback0'],
                    "status": "active",
                    "role": "loopback",
                    "tenant": {'name': 'PLDT', 'slug': 'pldt'},
                    "assigned_object_type": "dcim.interface",
                    'assigned_object_id': loopback0.id,
                    'assigned_object': {'id': loopback0.id, 'device': {'name': data['hostname']}}
                }
                try:
                    nb.ipam.ip_addresses.create(temp_loop0)
                except pynautobot.RequestError as e:
                    error_log.write("{0} {1}\n{2}\n".format(data['hostname'],x['ipv6_loopback0'], str(e.error)))
                    print(data['hostname'],x['ipv6_loopback0'])
                    print(e.error)
                    pass
            if dup_ip != None:
                error_log.write("{0} {1} already assigned\n".format(data['hostname'],x['ipv6_loopback0']))
                print(x['ipv6_loopback0']+ " already assigned")


        if nb.dcim.interfaces.get(name='Loopback1',device=data['hostname']) != None:
            loopback1=nb.dcim.interfaces.get(name='Loopback1',device=data['hostname'])
            dup_ip = nb.ipam.ip_addresses.get(assigned_object_id=loopback1.id,address=data['ipv6_loopback1'])
            if loopback1 != None and dup_ip == None:
                temp_loop1={
                    'address': data['ipv6_loopback1'],
                    "status": "active",
                    "role": "loopback",
                    "tenant": {'name': 'PLDT', 'slug': 'pldt'},
                    "assigned_object_type": "dcim.interface",
                    'assigned_object_id': loopback1.id,
                    'assigned_object': {'id': loopback1.id, 'device': {'name': data['hostname']}}
                }
                try:
                    nb.ipam.ip_addresses.create(temp_loop1)
                except pynautobot.RequestError as e:
                    error_log.write("{0} {1}\n{2}\n".format(data['hostname'],x['ipv6_loopback1'], str(e.error)))
                    print(data['hostname'],x['ipv6_loopback1'])
                    print(e.error)
                    pass
            if dup_ip != None:
                error_log.write("{0} {1} already assigned\n".format(data['hostname'],x['ipv6_loopback1']))
                print(x['ipv6_loopback1']+ " already assigned")

def assign_primary():
    devices=nb.dcim.devices.all()
    ip_add_all=nb.ipam.ip_addresses.all()
    for device in devices:
        for ip in ip_add_all:
            if device.name==ip.assigned_object.device.name:
                if ip.assigned_object.name == "Loopback1" and ip.family.value==4:
                    device.update({'primary_ip4': ip.id})
                elif ip.assigned_object.name == "Loopback1" and ip.family.value==6:
                    device.update({'primary_ip6': ip.id})


def assign_custom_device():
    devices=nb.dcim.devices.all()
    for i in p.nodes:
        data=p.nodes[i]
        for device in devices:
            if device.name==data['hostname']:
                if data['sid_absolute_prefix'] != None:
                    try:
                        device.update({'custom_fields': {'SID_ABSOLUTE_PREFIX' : data['sid_absolute_prefix']}})
                    except pynautobot.RequestError as e:
                        error_log.write("{0} {1}\n{2}\n".format(data['hostname'],data['sid_absolute_prefix'], str(e.error)))
                        print(e.error)
                        pass
                if data['sid_absolute_strict_prefix'] != None:
                    try:
                        device.update({'custom_fields': {'SID_ABSOLUTE_STRICT_PREFIX' : data['sid_absolute_strict_prefix']}})
                    except pynautobot.RequestError as e:
                        error_log.write("{0} {1}\n{2}\n".format(data['hostname'],data['sid_absolute_strict_prefix'], str(e.error)))

                        print(e.error)
                        pass
                if data['any_cast_sid'] != None:
                    try:
                        device.update({'custom_fields': {'ANY_CAST_SID' : data['any_cast_sid']}})
                    except pynautobot.RequestError as e:
                        error_log.write("{0} {1}\n{2}\n".format(data['hostname'],data['any_cast_sid'], str(e.error)))
                        print(e.error)
                        pass


def assign_custom_interfaces():
    interfaces=nb.dcim.interfaces.all()
    for i in p.nodes:
        data=p.nodes[i]
        for bundle in data["bundles"]:
            for interface in interfaces:
                if interface.device.name==data['hostname'] and bundle['source_bundle_interface'] == interface.name:
                    if bundle['agg_id'] != None:
                        try:
                            interface.update({'custom_fields': {'ISIS_AREA' : bundle['agg_id']}})
                        except pynautobot.RequestError as e:
                            error_log.write("{0} {1} {2}\n{3}\n".format(data['hostname'],bundle['agg_id'],bundle['source_bundle_interface'], str(e.error)))
                            print(e.error)
                            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--file', default="src/PLDT TNT PH2 - Port Mapping, IP Addressing and Device Information Draft.xlsx", help='Single Source of Trust Excel File')
    parser.add_argument('--links', default="port_mapping", help='Sheet name of Port mapping')
    parser.add_argument('--node', default="device_information", help='Sheet name of Device Information')
    args = parser.parse_args()
    nodes=load_data(args.file,args.node)

    site_list=api_node(nodes)[0]
    device_list=api_node(nodes)[1]
    add_site(site_list)
    add_device(device_list)

    p=xlsx_graph(args.file, args.node, args.links)
    add_loopback()
    add_bundle_interface()
    add_phy_interface()
    add_connection()
    assign_ipv4()
    assign_ipv6()
    assign_primary()
    assign_custom_interfaces()