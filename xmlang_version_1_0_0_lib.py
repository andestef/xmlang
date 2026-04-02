import xml.etree.ElementTree as ET
import re
from copy import deepcopy
class xmlang:
    class types:
        class funct:
            typeName = "funct"
            vars = {}
            def __init__(self,children, reqargs=[], optargs={}, takesChildren=False,allowlangcall=False,const=False):
                self.takesChildren = takesChildren
                self.children = children
                self.reqargs = reqargs
                self.optargs = optargs
                self.allowlangcall = allowlangcall
                self.const = const
            def make(caller, child):
                reqArgs = []
                optArgs = {}
                fargs = ['to',"takesChildren", "kwargs"]
                for i,v in child.attrib.items():
                    if not i in fargs:
                        if i == v:
                            reqArgs.append(i)
                        else:
                            optArgs[i] = caller._textProcess(v)
                if 'kwargs' in list(child.attrib.keys()) and optArgs == {}:
                    optArgs = None
                cl = []
                for i in child:
                    cl.append(i)
                f = caller.types.funct(cl,reqArgs,optArgs,'takesChildren' in list(child.attrib.keys()),False,'const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def onCall(self, caller, child):
                oag = caller._autoglob
                caller._autoglob = False
                odb = caller._langcall
                caller._langcall = self.allowlangcall
                usedOpts = []
                unusedReqs = deepcopy(self.reqargs)
                for i,v in child.attrib.items():
                    if i in self.reqargs:
                        caller.varset(i,caller._textProcess(v))
                        unusedReqs.remove(i)
                    elif i in self.optargs:
                        caller.varset(i,caller._textProcess(v))
                        usedOpts.append(i)
                    else:
                        caller.error("CallError",f"Call to {child.tag} has illegal argument {i}")
                for i,v in self.optargs.items():
                    if not i in usedOpts:
                        caller.varset(i,v)
                if unusedReqs != []:
                    caller.error("CallError",f"Call to {child.tag} missing required argument {unusedReqs[0]}")
                op = caller._cPath
                caller._cPath += "."+child.tag
                caller.run(self.children)
                caller._cPath = op
                caller._autoglob = oag
                caller._langcall = odb
            def toString(self):
                return f"Function with required args: {self.reqargs} and optional args {self.optargs}"
        class string:
            typeName = "string"
            vars = {}
            def onCall(self,caller, child):
                print(self.value)
            def make(caller, child):
                f = caller.types.string(caller._textProcess(child.text).toString(),'const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def __init__(self,value,const=False):
                self.value = value
                self.const = const
            def toString(self):
                return self.value
        class null:
            vars = {}
            typeName = "null"
            def onCall(self,caller, child):
                print("null")
            def __init__(self,const=False):
                self.const = const
            def make(caller, child):
                f = caller.types.null('const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def toString(self):
                return "null"
        class classType:
            typeName = "class"
            vars = {}
            def onCall(self,caller, child):
                if self.makeType == 'static':
                    n = deepcopy(child.attrib['to'])
                    del child.attrib['to']
                    ags = caller._autoGlob(False)
                    caller.varset('this',self)
                    if not self.name in self.vars:
                        caller.error("ClassError",f"Class {self.name} missing self named constructor")
                    op = caller._cPath
                    caller._cPath += '.'+child.tag
                    self.vars[self.name].onCall(caller,child)
                    caller._cPath = op
                    var = caller.varget('this')
                    caller._autoGlob(ags)
                    caller.varset(n,var)
                else:
                    n = deepcopy(child.attrib['to'])
                    del child.attrib['to']
                    ags = caller._autoGlob(False)
                    caller.varset('this',caller.types.classType(n,self.const,deepcopy(self.vars),'static'))
                    op = caller._cPath
                    caller._cPath += '.'+child.tag
                    self.vars[self.name].onCall(caller,child)
                    caller._cPath = op
                    var = caller.varget('this')
                    caller._autoGlob(ags)
                    caller.varset(n,var)
            def __init__(self,name,const,cvars,makeType):
                self.const = const
                self.name = name
                self.vars = cvars
                self.makeType = makeType
            def make(caller, child):
                t = 'static' if 'static' in child.attrib else 'instance'
                caller._setClass(child.attrib['to'],'const' in list(child.attrib.keys()),t)
                ags = caller._autoGlob(False)
                locs = caller._locsState()
                cl = []
                for i in child:
                    cl.append(i)
                op = caller._cPath
                caller._cPath += '.'+child.attrib['to']
                caller.run(cl)
                caller._cPath = op
                var = caller._endClass()
                caller._autoGlob(ags)
                caller._locsState(locs)
                if t == 'instance' and not child.attrib['to'] in list(var.vars.keys()):
                    caller.error("ClassError",f"Class {child.attrib['to']} missing self named constructor")
                caller.varset(child.attrib['to'],var)
            def toString(self):
                return f"Class {self.name} with children: {','.join([i.name for i in self.children])}."
        types = {"funct":funct,"string":string,"null":null,"class":classType}
    def __init__(self,langcall=False):
        self._globs = {}
        self._langcall = langcall
        self._autoglob = True
        self._locs = {}
        self._class = [self.types.null()]
        self._className = ""
        self._consts = []
        self._aSpec = 'public'
        self._retv = self.types.null()
        self._retr = False
        self._cPath = "main"
        self._buildBuiltins()
    def error(self,typ,reason="",fatal=True):
        print(f"XMLANG Error {typ}{' (fatal)' if fatal else ''}: {reason}.")
        if fatal:
            quit(1)
    def _autoGlob(self,state):
        a = self._autoglob
        self._autoglob = state
        return a
    def _setClass(self,name,const,maketype,vars={}):
        if self._className == '':
            self._className = name
        else:
            self._className += '.'+name
        self._class.insert(0,self.types.classType(self._className,const,vars,maketype))
    def _endClass(self):
        v = deepcopy(self._class[0])
        del self._class[0]
        cn = self._className[::-1].split('.')
        del cn[0]
        self._className = '.'.join(cn[::-1])
        return v
    def _locsState(self,sv=None):
        if sv == None:
            v = deepcopy(self._locs)
            self._locs = {}
            return v
        else:
            self._locs = sv
    def varset(self,name,data,glob=False):
        if name in self._consts:
            self.error("DefineError",f"Variable {name} is constant")
        if self._class[0].typeName != "null":
            self._class[0].vars[name] = data
        class vl:
            typeName = 'null'
            vars = self._locs
        s = name.split('.')
        for v in range(len(s)-1):
            i = s[v]
            if i in vl.vars:
                if vl.typeName == 'class' and vl.makeType == 'instance':
                    self.error("ClassError",f"Can not set value of instance class {vl.name} in {name}")
                vl = vl.vars[i]
            else:
                self.error("DefineError",f"Name {i} is not defined in {name}")
        vl.vars[s[-1]] = data
        if self._autoglob or glob:
            class vl:
                typeName = 'null'
                vars = self._globs
            s = name.split('.')
            for v in range(len(s)-1):
                i = s[v]
                if i in vl.vars:
                    if vl.typeName == 'class' and vl.makeType == 'instance':
                        return
                    vl = vl.vars[i]
                else:
                    return
            vl.vars[s[-1]] = data
    def varget(self,name):
        class vl:
            typeName = 'null'
            vars = {}
        for i,v in self._globs.items():
            vl.vars[i] = v
        for i,v in self._locs.items():
            vl.vars[i] = v
        for i in name.split('.'):
            if i in vl.vars:
                if vl.typeName == 'class' and vl.makeType == 'instance':
                    self.error("ClassError",f"Can not get value of instance class {vl.name} in {name}")
                vl = vl.vars[i]
            else:
                self.error("DefineError",f"Name {i} is not defined in {name}")
        return vl
    def varexists(self,name):
        e = True
        class vl:
            vars = {}
        for i,v in self._globs.items():
            vl.vars[i] = v
        for i,v in self._locs.items():
            vl.vars[i] = v
        for i in name.split('.'):
            if i in vl.vars:
                vl = vl.vars[i]
            else:
                e = False
                break
        return e
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
            elif child.tag in list(self.types.types.keys()):
                self.types.types[child.tag].make(self,child)
            elif self.varexists(child.tag):
                self.varget(child.tag).onCall(self,child)
            else:
                self.error("FunctError",f"Unknown tag: {child.tag}")
    def _textProcess(self,text):
        m = re.match(r"^[ \n\t]*\{var:[ \n\t]*([A-Za-z_\$]+[A-Za-z0-9_\.\$]*)[ \n\t]*\}[ \n\t]*$",text)
        if m:
            return self.varget(m[1])
        else:
            v = re.match(r"\{([^\}]*)\}",text)
            while v != None:
                text = text.replace(v[0],self.varget(v[1]).toString())
                v = re.match(r"\{([^\}]*)\}",text)
            return self.types.string(text)
    def _buildBuiltins(self):
        code = "<funct><langcall command='print' text='{var: text}'> </langcall></funct>"
        child = ET.fromstring(code)
        cl = []
        for i in child:
            cl.append(i)
        f = self.types.funct(cl,['text'],{},False,True)
        self.varset("print",f)
    def _tag_langcall(self,child):
        if not self._langcall:
            self.error("LangCallError","Current funct does not have langcall permissions")
        elif child.attrib['command'] == 'print':
            print(self._textProcess(child.attrib['text']).toString())
        elif child.attrib['command'] == 'rawvarprint':
            print(vars(self.varget(child.attrib['name'])))
        elif child.attrib['command'] == 'printvars':
            print("Locs: "+str(self._locs))
            print("Globs: "+str(self._globs))
        elif child.attrib['command'] == 'whereAmI':
            self.varset(child.attrib['to'],self.types.string(self._cPath,False))
    def addTag(self,tagname,data):
        self._tags[tagname] = data
    def _tag_public(self,child):
        self._aSpec = 'public'
        cl = []
        for i in child:
            cl.append(i)
        self.run(cl)
    _tags = {'langcall':{'f':_tag_langcall,'reqattrib':["command"],'optattrib':None,'takesChildren':True},'public':{"f":_tag_public,"reqattrib":[],"optattrib":[],'takesChildren':True}} #Optattrib=None is equiv to **kwargs