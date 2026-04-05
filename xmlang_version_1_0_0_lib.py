# As far as I can tell, this needs >= Python 3.8
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
            def onCall(self, caller, child, adv={}):
                oag = caller._autoglob
                caller._autoglob = False
                odb = caller._langcall
                caller._langcall = self.allowlangcall
                takeRet = 'to' in list(child.attrib.keys())
                if takeRet:
                    toVal = deepcopy(child.attrib['to'])
                    del child.attrib['to']
                usedOpts = []
                vts = {}
                unusedReqs = deepcopy(self.reqargs)
                for i,v in child.attrib.items():
                    if i in self.reqargs:
                        vts[i] = caller._textProcess(v)
                        unusedReqs.remove(i)
                    elif i in self.optargs:
                        vts[i] = caller._textProcess(v)
                        usedOpts.append(i)
                    else:
                        caller.error("CallError",f"Call to {child.tag} has illegal argument {i}")
                for i,v in self.optargs.items():
                    if not i in usedOpts:
                        vts[i] = v
                if unusedReqs != []:
                    caller.error("CallError",f"Call to {child.tag} missing required argument {unusedReqs[0]}")
                locs = caller._locsState()
                caller._locsState(adv)
                for i,v in vts.items():
                    caller.varset(i,v)
                op = caller._cPath
                caller._cPath += "."+child.tag
                caller.run(self.children)
                fvars = caller._locsState()
                caller._cPath = op
                caller._autoglob = oag
                caller._langcall = odb
                caller._locsState(locs)
                if takeRet:
                    rv = deepcopy(caller._retv)
                    caller.varset(toVal,rv)
                caller._retv = caller.types.null()
                caller._retr = False
                return fvars
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
                    op = caller._cPath
                    caller._cPath += '.'+child.tag
                    v = self.vars[self.name].onCall(caller,child,{'this':caller.types.classType(n,self.const,deepcopy(self.vars),'static')})
                    caller._cPath = op
                    var = v['this']
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
        class int:
            typeName = "int"
            vars = {}
            def onCall(self,caller, child):
                att = list(child.attrib.keys())
                to = 'to' in att
                fval = self.toInt()
                if to:
                    tv = deepcopy(child.attrib['to'])
                    del child.attrib['to']
                    att.remove('to')
                if 'exp' in att:
                    fval = int(fval**caller._textProcess(child.attrib['exp'],caller.types.int).toInt())
                if 'mult' in att and 'div' in att:
                    if att.index('mult')<att.index('div'): # Multiplication before division
                        fval = int(fval*caller._textProcess(child.attrib['mult'],caller.types.int).toInt())
                        fval = int(fval/caller._textProcess(child.attrib['div'],caller.types.int).toInt())
                    else:
                        fval = int(fval/caller._textProcess(child.attrib['div'],caller.types.int).toInt())
                        fval = int(fval*caller._textProcess(child.attrib['mult'],caller.types.int).toInt())
                elif 'mult' in att:
                    fval = int(fval*caller._textProcess(child.attrib['mult'],caller.types.int).toInt())
                elif 'div' in att:
                    fval = int(fval/caller._textProcess(child.attrib['div'],caller.types.int).toInt())
                if 'add' in att and 'subtr' in att:
                    if att.index('add')<att.index('subtr'): # Multiplication before division
                        fval = int(fval+caller._textProcess(child.attrib['add'],caller.types.int).toInt())
                        fval = int(fval-caller._textProcess(child.attrib['subtr'],caller.types.int).toInt())
                    else:
                        fval = int(fval-caller._textProcess(child.attrib['subtr'],caller.types.int).toInt())
                        fval = int(fval+caller._textProcess(child.attrib['add'],caller.types.int).toInt())
                elif 'add' in att:
                    fval = int(fval+caller._textProcess(child.attrib['add'],caller.types.int).toInt())
                elif 'subtr' in att:
                    fval = int(fval-caller._textProcess(child.attrib['subtr'],caller.types.int).toInt())
                if to:
                    caller.varset(tv,caller.types.int(str(fval)))
                else:
                    self.value = str(fval)
            def __init__(self,val,const=False):
                self.value = val
            def toInt(self):
                return int(self.value)
            def make(caller, child):
                val = caller._textProcess(child.text).toString()
                v = ''
                pos = 0
                dot = False
                for i in val:
                    if dot:
                        pass
                    elif i == '-':
                        if pos != 0:
                            caller.error("TypeError","Can not have negative symbol not at begining of int.")
                        else:
                            v += '-'
                    elif i == '0':
                        if pos != 0:
                            v += '0'
                    elif i == '1':
                        v += '1'
                    elif i == '2':
                        v += '2'
                    elif i == '3':
                        v += '3'
                    elif i == '4':
                        v += '4'
                    elif i == '5':
                        v += '5'
                    elif i == '6':
                        v += '6'
                    elif i == '7':
                        v += '7'
                    elif i == '8':
                        v += '8'
                    elif i == '9':
                        v += '9'
                    elif i == '.':
                        dot = True
                    else:
                        caller.error("TypeError",f"Illegal character in int: \"{i}\"")
                    pos += 1
                f = caller.types.int(v,'const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def toString(self):
                return self.value
        types = {"funct":funct,"string":string,"null":null,"class":classType,'int':int}
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
                return False
        return True
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
            if self._retr and self._cPath != 'main':
                return
    def _textProcess(self,text,cast=types.string):
        m = re.match(r"^[ \n\t]*\{var:[ \n\t]*([A-Za-z_\$]+[A-Za-z0-9_\.]*)[ \n\t]*\}[ \n\t]*$",text)
        if m:
            return self.varget(m[1])
        else:
            v = re.finditer(r"(^|[^\\])(\{[ \n\t]*([^\} \n\t]*)[ \n\t]*(?=\}))",text)
            for i in v:
                text = text.replace(i[2]+'}',self.varget(i[3]).toString())
            v = re.finditer(r"\\(\{[ \n\t]*([^\} \n\t]*)[ \n\t]*\})",text)
            for i in v:
                text = text.replace(i[0],i[1])
            return cast(text)
    def _buildBuiltins(self):
        code = """<outer>
        <builtinvar-print><langcall command='print' text='{var: text}'> </langcall></builtinvar-print>
        <buildvar-builtin-current><langcall command='whereAmI-2' to='ret'> </langcall><return>{var: ret}</return></buildvar-builtin-current>
        <buildvar-builtin-textprocess><return>{var: data}</return></buildvar-builtin-textprocess>
        <buildvar-math-add><int to='v1'>{v1}</int><v1 add='{v2}' /><return>{var: v1}</return></buildvar-math-add>
        <buildvar-math-subtr><int to='v1'>{v1}</int><v1 subtr='{v2}' /><return>{var: v1}</return></buildvar-math-subtr>
        <buildvar-math-mult><int to='v1'>{v1}</int><v1 mult='{v2}' /><return>{var: v1}</return></buildvar-math-mult>
        <buildvar-math-div><int to='v1'>{v1}</int><v1 div='{v2}' /><return>{var: v1}</return></buildvar-math-div>
        <buildvar-math-exp><int to='v1'>{v1}</int><v1 exp='{v2}' /><return>{var: v1}</return></buildvar-math-exp>
        </outer>"""
        child = ET.fromstring(code)
        children = [i for i in child]
        f = self.types.funct([i for i in children[0]],['text'],{},False,True,True)
        self.varset("print",f)
        cvars = {}
        cvars['current'] = self.types.funct([i for i in children[1]],[],{},False,True)
        cvars['textprocess'] = self.types.funct([i for i in children[2]],['data'],{},False,True)
        self.varset("builtins",self.types.classType("builtins",True,cvars,'static'))
        cvars = {}
        cvars['add'] = self.types.funct([i for i in children[3]],['v1','v2'],{},False,True)
        cvars['subtr'] = self.types.funct([i for i in children[4]],['v1','v2'],{},False,True)
        cvars['mult'] = self.types.funct([i for i in children[5]],['v1','v2'],{},False,True)
        cvars['div'] = self.types.funct([i for i in children[6]],['v1','v2'],{},False,True)
        cvars['exp'] = self.types.funct([i for i in children[7]],['v1','v2'],{},False,True)
        self.varset("math",self.types.classType("math",True,cvars,'static'))
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
        elif child.attrib['command'] == 'whereAmI-2':
            v = self._cPath[::-1].replace(self._cPath.split(".")[-1][::-1]+'.',"",1)[::-1]
            v = v[::-1].replace(v.split(".")[-1][::-1]+'.',"",1)[::-1]
            self.varset(child.attrib['to'],self.types.string(v,False))
    def addTag(self,tagname,data):
        self._tags[tagname] = data
    def _tag_public(self,child):
        if self._className == '':
            self.error("ClassError","Can not set access modifier when not in a class")
        self._aSpec = 'public'
        cl = []
        for i in child:
            cl.append(i)
        self.run(cl)
    def _tag_return(self,child):
        self._retr = True
        self._retv = self._textProcess(child.text)
    _tags = {'langcall':{'f':_tag_langcall,'reqattrib':["command"],'optattrib':None,'takesChildren':True},'public':{"f":_tag_public,"reqattrib":[],"optattrib":[],'takesChildren':True},'return':{'f':_tag_return,'reqattrib':[],'optattrib':[],'takesChildren':True}} #Optattrib=None is equiv to **kwargs
