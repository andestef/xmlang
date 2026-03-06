import xml.etree.ElementTree as ET
from lxml import etree
import re
parser = etree.XMLParser(recover=True)
s = open('test.xmlang').read()
root = etree.fromstring(s, parser)
from importlib import import_module
tree = ET.fromstring(etree.tostring(root).decode('utf-8'))
root = list(tree.iter())[0]
if root.tag != "xmlang":
    print("XMLANG Error: Missing <xmlang> opening tag.")
if not "version" in root.attrib:
    version = '1.0.0'
else:
    version = root.attrib['version']
v = import_module(f"xmlang.version.{version}.lib".replace(".","_"))
lang = v.xmlang()
lang.run(root)