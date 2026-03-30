import xml.etree.ElementTree as ET
from importlib import import_module
# uncomment to use command line mode and add comment next line
filename = 'test.xmlang'
'''from sys import argv
filename = argv[1]'''
# If you don't want to use lxml comment from here to the next comment, then uncomment that line
from lxml import etree
parser = etree.XMLParser(recover=True)
s = open(filename).read()
tree = etree.fromstring(s, parser)
root = ET.fromstring(etree.tostring(tree).decode('utf-8'))
#root = ET.fromstring(open(filename).read())
if root.tag != "xmlang":
    print("XMLANG Error: Missing <xmlang> opening tag.")
if not "version" in root.attrib:
    version = '1.0.0'
else:
    version = root.attrib['version']
v = import_module(f"xmlang.version.{version}.lib".replace(".","_"))
lang = v.xmlang()
lang.run(root)