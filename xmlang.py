import xml.etree.ElementTree as ET
from importlib import import_module
tree = ET.parse('test.xmlang')
root = tree.getroot()
if root.tag != "xmlang":
    print("XMLANG Error: Missing <xmlang> opening tag.")
if not "version" in root.attrib:
    version = '1.0.0'
else:
    version = root.attrib['version']
v = import_module(f"xmlang.version.{version}.lib".replace(".","_"))
lang = v.xmlang()
lang.run(root)