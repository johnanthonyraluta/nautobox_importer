from pprint import pprint
import pynautobot,json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

try:
    nb.dcim.regions.create({"name": "GMM", 'slug': "gmm", 'description': "Greater Metro Manila"})
    nb.dcim.regions.create({"name": "NL", 'slug': "nl", 'description': "North Luzon"})
    nb.dcim.regions.create({"name": "SL", 'slug': "sl", 'description': "South Luzon"})

except pynautobot.RequestError as e:
    print(e.error)
    pass



try:
    nb.tenancy.tenants.create({"name": "PLDT", 'slug': "pldt"})
except pynautobot.RequestError as e:
    print(e.error)
    pass

try:
    nb.dcim.manufacturers.create({"name": "Cisco", 'slug': "cisco"})
except pynautobot.RequestError as e:
    print(e.error)
    pass

try:
    nb.dcim.platforms.create({"name": "IOS-XR", 'slug': "ios-xr","manufacturer": nb.dcim.manufacturers.get(name="Cisco").id})
except pynautobot.RequestError as e:
    print(e.error)
    pass

device_types = [
{
  "manufacturer": nb.dcim.manufacturers.get(name="Cisco").id,
  "model": "ASR9910",
  "slug": "asr9910",
  "u_height": 8,
  "is_full_depth": True
},
{
  "manufacturer": nb.dcim.manufacturers.get(name="Cisco").id,
  "model": "NCS5504",
  "slug": "ncs5504",
  "u_height": 4,
  "is_full_depth": True
},
{
  "manufacturer": nb.dcim.manufacturers.get(name="Cisco").id,
  "model": "NCS5508",
  "slug": "ncs5508",
  "u_height": 8,
  "is_full_depth": True
},
{
  "manufacturer": nb.dcim.manufacturers.get(name="Cisco").id,
  "model": "Virtual Router",
  "slug": "virtual_router",
  "u_height": 0,
  "is_full_depth": False
}
]


device_roles= [
{
  "name": "AN",
  "slug": "an",
  "color": "00bcd4",
  "vm_role": False
},
{
  "name": "ASBR",
  "slug": "asbr",
  "color": "ffc107",
  "vm_role": False
},
{
  "name": "DN",
  "slug": "dn",
  "color": "4caf50",
  "vm_role": False
},
{
  "name": "P",
  "slug": "p",
  "color": "607d8b",
  "vm_role": False
},
{
  "name": "PE",
  "slug": "pe",
  "color": "ffeb3b",
  "vm_role": False
},
{
  "name": "S-RR",
  "slug": "s-rr",
  "color": "03a9f4",
  "vm_role": True
},
{
  "name": "T-RR",
  "slug": "t-rr",
  "color": "ff66ff",
  "vm_role": True
},
{
  "name": "XTC",
  "slug": "xtc",
  "color": "f44336",
  "vm_role": True
}
]


for types in device_types:
    try:
        nb.dcim.device_types.create(types)
    except pynautobot.RequestError as e:
        print(e.error)
        pass
for roles in device_roles:
    try:
        nb.dcim.device_roles.create(roles)
    except pynautobot.RequestError as e:
        print(e.error)
        pass

custom_fields= [
    {
      "content_types": ["dcim.device"],
      "type": "integer",
      "name": "ANY_CAST_SID",
      "required": False,
    },
    {
      "content_types": ["dcim.interface"],
      "type": "integer",
      "name": "ISIS_AREA",
      "required": False
    },
    {
      "content_types": ["dcim.device"],
      "type": "integer",
      "name": "SID_ABSOLUTE_PREFIX",
      "required": False
    },
    {
      "content_types": ["dcim.device"],
      "type": "integer",
      "name": "SID_ABSOLUTE_STRICT_PREFIX",
      "required": False,
    }]

for field in custom_fields:
    try:
        nb.extras.custom_fields.create(field)
    except pynautobot.RequestError as e:
        print(e.error)
        pass
