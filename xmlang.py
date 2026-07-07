from importlib import import_module
commandline_mode = False #Use static filename or get filename from argv
use_lxml = True #Use libary lxml (install with pip install lxml)
if not commandline_mode:
    filename = 'test.xmlang'
else:
    from sys import argv
    filename = argv[1]
if use_lxml:
    from lxml import etree as ET
    parser = ET.XMLParser(recover=True)
    s = open(filename).read()
    root = ET.fromstring(s, parser)
else:
    import xml.etree.ElementTree as ET
    root = ET.fromstring(open(filename).read())
if root.tag != "xmlang":
    print("XMLANG Error: Missing <xmlang> opening tag.")
if not "version" in root.attrib:
    version = '1.0.0'
else:
    version = root.attrib['version']
v = import_module(f"xmlang.version.{version}.lib".replace(".","_"))
lang = v.xmlang(ET)
lang.run(root)