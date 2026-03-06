import xml.etree.ElementTree as ET
import re
class xmlang:
    class types:
        class funct:
            typeName = "funct"
            def __init__(self,children, reqargs=[], optargs={}, takesChildren=False,allowlangcall=True):
                self.takesChildren = takesChildren
                self.children = children
                self.reqargs = reqargs
                self.optargs = optargs
                self.allowlangcall = allowlangcall
            def onCall(self,caller, child):
                oag = caller._autoglob
                caller._autoglob = False
                odb = caller._langcall
                caller._langcall = self.allowlangcall
                usedOpts = []
                unusedReqs = self.reqargs
                for i,v in child.attrib.items():
                    if i in self.reqargs:
                        caller.varset(i,caller._textProcess(v))
                        unusedReqs.remove(i)
                    elif i in self.optArgs:
                        caller.varset(i,caller._textProcess(v))
                        usedOpts.append(i)
                    else:
                        caller.error("CallError",f"Call to {child.tag} has illegal argument {i}")
                for i,v in self.optargs.items():
                    if not i in usedOpts:
                        caller.varset(i,v)
                if unusedReqs != []:
                    caller.error("CallError",f"Call to {child.tag} missing required argument {unusedReqs[0]}")
                caller.run(self.children)
                caller._autoglob = oag
                caller._langcall = odb
            def toString(self):
                return f"Function with required args: {self.reqargs} and optional args {self.optargs}"
        class string:
            typeName = "string"
            def onCall(self,caller, child):
                print(self.value)
            def __init__(self,value):
                self.value = value
            def toString(self):
                return self.value
        class null:
            typeName = "null"
            def onCall(self,caller, child):
                print("null")
            def __init__(self):
                pass
            def toString(self):
                return "null"
    def __init__(self,langcall=False):
        self._globs = {}
        self._langcall = langcall
        self._autoglob = True
        self._locs = {}
        self._consts = []
        self._retv = self.types.null()
        self._buildBuiltins()
    def error(self,typ,reason="",fatal=True):
        print(f"XMLANG Error {typ}{' (fatal)' if fatal else ''}: {reason}.")
        if fatal:
            quit(1)
    def varset(self,name,data,glob=False):
        if name in self._consts:
            self.error("DefineError",f"Variable {name} is constant")
        self._locs[name] = data
        if self._autoglob or glob:
            self._globs[name] = data
    def varget(self,name):
        if name in self._locs:
            return self._locs[name]
        elif name in self._globs:
            return self._globs[name]
        else:
            self.error("DefineError",f"Name {name} is not defined")
    def varexists(self,name):
        return name in self._locs or name in self._globs
    def run(self,tree):
        for child in tree:
            if child.tag in self._tags:
                for i in self._tags[child.tag]['reqattrib']:
                    if not i in child.attrib:
                        self.error("CallError",f"Call to {child.tag} missing required argument {i}")
                if self._tags[child.tag]['optattrib'] != None: 
                    for i in child.attrib:
                        if not i in self._tags[child.tag]['reqattrib'] and not i in self._tags[child.tag]['optattrib']:
                            self.error("CallError",f"Call to {child.tag} has illegal argument {i}")
                if child.text != None or len(child) != 0:
                    if not self._tags[child.tag]['takesChildren']:
                        self.error("CallError",f"Call to {child.tag} does not accept children")
                if self._tags[child.tag]['takesChildren'] and child.text == None and len(child) == 0:
                    self.error("CallError",f"Call to {child.tag} missing child value")
                self._tags[child.tag]['f'](self,child)
            elif self.varexists(child.tag):
                self.varget(child.tag).onCall(self,child)
            else:
                self.error("FunctError",f"Unknown tag: {child.tag}")
    def _textProcess(self,text):
        v = re.match(r"\{([^\}]*)\}",text)
        while v != None:
            text = text.replace(v[0],self.varget(v[1]).toString())
            v = re.match(r"\{([^\}]*)\}",text)
        return self.types.string(text)
    def _buildBuiltins(self):
        code = "<funct><langcall command='print'>{text}</langcall></funct>"
        child = ET.fromstring(code)
        f = self.types.funct(list(list(child.iter())[0].iter())[0],[],{},False,True)
        self.varset("printhi",f)
    def _tag_funct(self,child):
        reqArgs = []
        optArgs = {}
        fargs = ['name',"takesChildren", "kwargs"]
        for i,v in child.attrib.items():
            if not i in fargs:
                if i == v:
                    reqArgs.append(i)
                else:
                    optArgs[i] = self._textProcess(v)
        if 'kwargs' in list(child.attrib.keys()) and optArgs == {}:
            optArgs = None
        f = self.types.funct(child.iter(),reqArgs,optArgs,'takesChildren' in list(child.attrib.keys()))
        self.varset(child.attrib['name'],f)
    def _tag_langcall(self,child):
        if not self._langcall:
            self.error("LangCallError","Current funct does not have langcall permissions")
        if child.attrib['command'] == 'print':
            print(self._textProcess(child.attrib['text']))
    def addTag(self,tagname,data):
        self._tags[tagname] = data
    _tags = {'funct':{"f":_tag_funct,'reqattrib':["name"],'optattrib':None,'takesChildren':True},'langcall':{'f':_tag_langcall,'reqattrib':["command"],'optattrib':None,'takesChildren':True}} #Optattrib=None is equiv to **kwargs