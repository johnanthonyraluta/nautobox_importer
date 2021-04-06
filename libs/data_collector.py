import collections,json
import subprocess,requests

#local libs
from xlsx_handler import xlsx_handler

class xlsx_graph:
    def __init__(self, filename, node_sheet, links_sheet):
        self.filename=filename
        self.nodes = collections.defaultdict(dict)
        self.node_sheet=node_sheet
        self.links_sheet=links_sheet
        self.node_list=[]
        self.links_list=[]
        self._init_nodes(node_sheet,links_sheet)

    def _init_nodes(self, node_sheet,links_sheet):
        xl=xlsx_handler(self.filename)
        self.node_list=xl.read_all(node_sheet)
        self.links_list=xl.read_all(links_sheet)
        
        for i in self.node_list:
            node=i["hostname"]
            if node==None:
                continue
            node=node.strip()
            self.nodes[node]['site_name']=i['site_name']
            self.nodes[node]['device_type']=self._device_type(i["device_type"])
            self.nodes[node]['hostname']=node
            self.nodes[node]['region']=str(i["region"])
            self.nodes[node]["ipv4_loopback0"]=str(i["ipv4_loopback0_address"])
            self.nodes[node]["ipv6_loopback0"]=str(i["ipv6_loopback0_address"])
            self.nodes[node]["ipv4_loopback1"]=str(i["ipv4_management_ip"])
            self.nodes[node]["ipv6_loopback1"]=str(i["ipv6_management_ip"])
            self.nodes[node]["ipv4_loopback100"]=i["ipv4_anycast_ip"]
            self.nodes[node]["sid_absolute_prefix"]=i["sid_asolute_prefix"]
            self.nodes[node]["sid_absolute_strict_prefix"]=i["sid_absolute_strict_prefix"]
            self.nodes[node]["any_cast_sid"]=i["any_cast_sid"]
            self.nodes[node]["phase"]=i["phase 1"]
            self.nodes[node]["bundles"]=[]
            self.nodes[node]["interfaces"]=[]
            self.nodes[node]['isis_lo0']=self._isis_lo0(i["ipv4_loopback0_address"])
            self.nodes[node]['snmp_engineid']=self._snmp_engineid(i["ipv4_loopback0_address"])


##Build interface list
            bundle_count=[]
            for j in self.links_list:
                if j["hostname"]==node and j['target_hostname'] != None and j["source_bundle_interface"] != None:
                    if 'HundredGigE' not in j["source_interface_id"] and type(j["source_interface_id"])==str:
                       source_interface= 'HundredGigE'+ j["source_interface_id"]
                    else:
                       source_interface= j["source_interface_id"]
                    if type(j["target_interface_id"])==str and 'HundredGigE' not in j["target_interface_id"] :
                       target_interface= 'HundredGigE'+ j["target_interface_id"]
                    else:
                       target_interface= j["target_interface_id"]

                    interface_dict={
                    "source_hostname" : j["hostname"],
                    "source_region" : j["source_region"],
                    "source_site" : j["source_site"],
                    "source_device_type" : self._device_type(str(j["source_device_type"])),
                    'source_interface_id': source_interface,
                    "source_bundle_interface" : j["source_bundle_interface"],
                    "source_bundle_ipv4" : j["source_ipv4_address"],
                    "source_bundle_ipv6" : j["source_ipv6_address"],
                    "target_hostname" : j["target_hostname"],
                    "target_region" : j["target_region"],
                    "target_site" : j["target_site"],
                    "target_device_type" : self._device_type(str(j["target_device_type"])),
                    'target_interface_id': target_interface,
                    "target_bundle_interface" : j["target_bundle_interface"],
                    "target_bundle_ipv4" : j["target_ipv4_address"],
                    "target_bundle_ipv6" : j["target_ipv6_address"]
                    }
                    self.nodes[node]["interfaces"].append(interface_dict)

                elif j["target_hostname"]==node and j['hostname'] != None:
                    if 'HundredGigE' not in j["source_interface_id"] and type(j["source_interface_id"])==str:
                       target_interface= 'HundredGigE'+ j["source_interface_id"]
                    else:
                       target_interface= j["source_interface_id"]
                    if 'HundredGigE' not in j["target_interface_id"] and type(j["target_interface_id"])==str:
                       source_interface= 'HundredGigE'+ j["target_interface_id"]
                    else:
                       source_interface= j["target_interface_id"]

                    interface_dict={
                    "target_hostname" : j["hostname"],
                    "target_region" : j["source_region"],
                    "target_site" : j["source_site"],
                    "target_device_type" : self._device_type(str(j["source_device_type"])),
                    'target_interface_id': target_interface,
                    "target_bundle_interface" : j["source_bundle_interface"],
                    "target_bundle_ipv4" : j["source_ipv4_address"],
                    "target_bundle_ipv6" : j["source_ipv6_address"],
                    "source_hostname" : j["target_hostname"],
                    "source_region" : j["target_region"],
                    "source_site" : j["target_site"],
                    "source_device_type" : self._device_type(str(j["target_device_type"])),
                    'source_interface_id': source_interface,
                    "source_bundle_interface" : j["target_bundle_interface"],
                    "source_bundle_ipv4" : j["target_ipv4_address"],
                    "source_bundle_ipv6" : j["target_ipv6_address"],
                    }
                    self.nodes[node]["interfaces"].append(interface_dict)

##Build bundle list
##Removing repeated bundle
                if j["hostname"]==node and (j['source_interface_id'] != None or j['target_interface_id'] != None)  and j["source_bundle_interface"] != None:
                    bundle_dict={
                    "source_hostname": j['hostname'],
                    "source_device_type" : self._device_type(str(j["source_device_type"])),
                    "source_bundle_interface" : j["source_bundle_interface"],
                    "source_bundle_ipv4" : j["source_ipv4_address"],
                    "source_bundle_ipv6" : j["source_ipv6_address"],
                    "target_hostname": j['target_hostname'],
                    "target_device_type" : self._device_type(str(j["target_device_type"])),
                    "target_bundle_interface" : j["target_bundle_interface"],
                    "target_bundle_ipv4" : j["target_ipv4_address"],
                    "target_bundle_ipv6" : j["target_ipv6_address"],
                    "agg_id": j['isis_area'],
                    "count": None,
                    "isis_metric": self._isis_metric(str(j['source_device_type']), str(j['target_device_type']))
                    }
                    bundle_count.append({'bundle_id': j['source_bundle_interface'], 'agg_id': j['isis_area'] })
                    self.nodes[node]["bundles"].append(bundle_dict)

                elif j["target_hostname"]==node and (j['source_interface_id'] != None or j['target_interface_id'] != None)  and j["target_bundle_interface"] != None:
                    bundle_dict={
                    "target_hostname": j['hostname'],
                    "target_device_type" : self._device_type(str(j["source_device_type"])),
                    "target_bundle_interface" : j["source_bundle_interface"],
                    "target_bundle_ipv4" : j["source_ipv4_address"],
                    "target_bundle_ipv6" : j["source_ipv6_address"],
                    "source_hostname": j['target_hostname'],
                    "source_device_type" : self._device_type(str(j["target_device_type"])),
                    "source_bundle_interface" : j["target_bundle_interface"],
                    "source_bundle_ipv4" : j["target_ipv4_address"],
                    "source_bundle_ipv6" : j["target_ipv6_address"],
                    "agg_id": j['isis_area'],
                    "count": None,
                    "isis_metric": self._isis_metric(str(j['target_device_type']), str(j['source_device_type']))
                    }
                    bundle_count.append({'bundle_id': j['target_interface_id'], 'agg_id': j['isis_area']})
                    self.nodes[node]["bundles"].append(bundle_dict)
                ##Remove duplicate
                bundle_list=[]
                seen = set()
                
                for dic in self.nodes[node]["bundles"]:
                    key = (dic['source_bundle_interface'])
                    if key in seen:
                        continue
                    bundle_list.append(dic)
                    seen.add(key)
                
                self.nodes[node]["bundles"] = bundle_list

                interface_list=[]
                seen_int = set()
                
                for dic in self.nodes[node]["interfaces"]:
                    key = (dic['source_interface_id'])
                    if key in seen_int:
                        continue
                    interface_list.append(dic)
                    seen_int.add(key)
                
                self.nodes[node]["interfaces"] = interface_list

                unique_counts = collections.Counter(e['bundle_id'] for e in bundle_count)


                for x in self.nodes[node]["interfaces"]:
                    x['count']=unique_counts[x['source_interface_id']]


    def _isis_lo0(self, lo):
        try:
            tmp=lo.replace("/32","")
            tmp=tmp.split(".")
            if len(tmp)==4:
                lo0="%03d.%03d.%03d.%03d"%(int(tmp[0]),int(tmp[1]),int(tmp[2]),int(tmp[3]))
                lo0=lo0.replace(".","")
                lo0='.'.join(lo0[i:i+4] for i in range(0, len(lo0), 4))
                return lo0
        except:
            return "0000.0000.0000"

    def _isis_metric(self,source_device_type,target_device_type):
        source_device_type=self._device_type(source_device_type)
        dst_device_type=self._device_type(target_device_type)

        cost=int()
    
        if source_device_type=='P' and dst_device_type=='P':
            cost=int(100)
        elif source_device_type=='P' and dst_device_type=='PE':
            cost=int(100)
        elif source_device_type=='P' and dst_device_type=='ASBR':
            cost=int(100)
        elif source_device_type=='PE' and dst_device_type=='P':
            cost=int(100)
        elif source_device_type=='ASBR' and dst_device_type=='P':
            cost=int(100)
        elif source_device_type=='PE' and dst_device_type=='PE':
            cost=int(1000)
        elif source_device_type=='ASBR' and dst_device_type=='ASBR':
            cost=int(1000)
        elif source_device_type=='PE' and dst_device_type=='DN':
            cost=int(1000)
        elif source_device_type=='PE' and dst_device_type=='AN':
            cost=int(1000)
        elif source_device_type=='AN' and dst_device_type=='PE':
            cost=int(1000)
        elif source_device_type=='DN' and dst_device_type=='PE':
            cost=int(1000)
        elif source_device_type=='DN' and dst_device_type=='AN':
            cost=int(1000)
        elif source_device_type=='DN' and dst_device_type=='DN':
            cost=int(1000)
        elif source_device_type=='AN' and dst_device_type=='DN':
            cost=int(1000)
        elif source_device_type=='AN' and dst_device_type=='AN':
            cost=int(1000)
        else:
            cost=None
        return cost

    
    def _snmp_engineid(self, lo0):
        hx=None
        if lo0==None:
            return None
        if "/" in lo0:
            hx=lo0.split('/')[0]
        else:
            hx=lo0
        hx=hx.split(".")
        if len(hx)==4:
            txt="%02X:%02X:%02X:%02X"%(int(hx[0]),int(hx[1]),int(hx[2]),int(hx[3]))
            return '80:00:00:09:01:'+txt
        else:
            return None

    def hostname2code(self,hostname):
        if "CICU" in hostname:
            device_type="AN"
        if "CICN" in hostname:
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
    
    def _device_type(self,device_type):
        if "PE-" in device_type:
            return "PE"
        if "P-" in device_type:
            return "P"
        elif "AN-" in device_type:
            return "AN"
        elif "DN-" in device_type:
            return "DN"
        elif "ASBR" in device_type:
            return "ASBR"
        else:
            return None



if __name__ == "__main__":
    from pprint import pprint
    filename='../src/PLDT TNT PH2 - Port Mapping, IP Addressing and Device Information Draft.xlsx'
    node_sheet='device_information'
    links_sheet='port_mapping'
    d1=xlsx_graph(filename,node_sheet,links_sheet)
    data=d1.nodes['BAT00B04CICN001']
    pprint(data)
