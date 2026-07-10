# As far as I can tell, this needs >= Python 3.8
import re
from copy import deepcopy
class xmlang:
    class types:
        class __type:
            typeName = "null"
            vars = {}
            isClass = False
            def onCall(self,caller, child):
                print(self.value)
            def toString(self,caller):
                return self.value
            def toInt(self,caller):
                return int(self.value)
            def equivto(self,caller,comp):
                if self.toString(caller)() == comp.toString(caller):
                    return True
                else:
                    return False
        class funct(__type):
            typeName = "funct"
            vars = {}
            def __init__(self,caller,children, reqargs=[], optargs={}, takesChildren=False,allowlangcall=False,const=False):
                self.vars['type'] = caller.types.type(caller,'funct',True)
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
                f = caller.types.funct(caller,cl,reqArgs,optArgs,'takesChildren' in list(child.attrib.keys()),False,'const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def onCall(self, caller, child, adv={}):
                child = deepcopy(child)
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
                caller._cPath += ","+child.tag+""
                caller.run(self.children)
                fvars = caller._locsState()
                caller._cPath = op
                caller._autoglob = oag
                caller._langcall = odb
                caller._locsState(locs)
                if takeRet:
                    rv = deepcopy(caller._retv)
                    caller.varset(toVal,rv)
                caller._retv = caller.types.null(caller)
                caller._retr = False
                return fvars
            def toString(self,caller):
                return f"Function with required args: {self.reqargs} and optional args {self.optargs}"
            def equivto(self,caller,comp):
                if self.toString(caller)() == comp.toString(caller)():
                    return True
                else:
                    return False
        class string(__type):
            typeName = "string"
            vars = {}
            def onCall(self,caller, child):
                if 'to' in child.attrib:
                    caller.varset(child.attrib['to'],caller.types.types[self.typeName](caller,self.value,'const' in child.attrib))
                else:
                    print(self.value)
            def make(caller, child):
                if child.text == None:
                    t = ""
                else:
                    t = child.text
                f = caller.types.string(caller,caller._textProcess(t).toString(caller),'const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def __init__(self,caller,value,const=False,endloop=0):
                if endloop < 2:
                    self.vars['type'] = caller.types.type(caller,self.typeName,True,endloop+1)
                else:
                    self.vars['type'] = 'psudotype'
                self.value = value
                self.const = const
            def toString(self,caller):
                return self.value
            def equivto(self,caller,comp):
                if self.toString(caller) == comp.toString(caller):
                    return True
                else:
                    return False
        class null(__type):
            vars = {}
            typeName = "null"
            def onCall(self,caller, child):
                if 'to' in child.attrib:
                    caller.varset(child.attrib['to'],caller.types.null(caller,'const' in child.attrib))
                else:
                    print('null')
            def __init__(self,caller,const=False):
                self.vars['type'] = caller.types.type(caller,'null',True)
                self.const = const
            def make(caller, child):
                f = caller.types.null(caller,'const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def toString(self,caller):
                return "null"
            def equivto(self,caller,comp):
                if comp.type == 'null':
                    return True
                else:
                    return False
        class classType(__type):
            typeName = "class"
            vars = {}
            isClass = True
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
                    v = self.vars[self.name].onCall(caller,child,{'this':caller.types.classType(caller,n,self.const,deepcopy(self.vars),'static',n)})
                    caller._cPath = op
                    var = v['this']
                    caller._autoGlob(ags)
                    caller.varset(n,var)
            def __init__(self,caller,name,const,cvars,makeType,typeN='class'):
                self.const = const
                self.name = name
                self.vars = cvars
                self.makeType = makeType
                self.vars['type'] = caller.types.string(caller,typeN,True)
                self.typeName = typeN
            def make(caller, child):
                t = 'static' if 'static' in child.attrib else 'instance'
                caller._setClass(child.attrib['to'],'const' in list(child.attrib.keys()),t,typeN=child.attrib['to'] if t == 'static' else 'class')
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
            def toString(self,caller):
                return f"Class {self.name} with children: {','.join([i.name for i in self.children])}."
            def equivto(self,caller,comp):
                if self.toString(caller)() == comp.toString(caller):
                    return True
                else:
                    return False
        class int(__type):
            typeName = "int"
            vars = {}
            def onCall(self,caller, child):
                att = list(child.attrib.keys())
                to = 'to' in att
                fval = self.toInt(caller)
                if to:
                    tv = deepcopy(child.attrib['to'])
                    del child.attrib['to']
                    att.remove('to')
                if 'exp' in att:
                    fval = int(fval**caller._textProcess(child.attrib['exp'],caller.types.int).toInt(caller))
                if 'mult' in att and 'div' in att:
                    if att.index('mult')<att.index('div'): # Multiplication before division
                        fval = int(fval*caller._textProcess(child.attrib['mult'],caller.types.int).toInt(caller))
                        fval = int(fval/caller._textProcess(child.attrib['div'],caller.types.int).toInt(caller))
                    else:
                        fval = int(fval/caller._textProcess(child.attrib['div'],caller.types.int).toInt(caller))
                        fval = int(fval*caller._textProcess(child.attrib['mult'],caller.types.int).toInt(caller))
                elif 'mult' in att:
                    fval = int(fval*caller._textProcess(child.attrib['mult'],caller.types.int).toInt(caller))
                elif 'div' in att:
                    fval = int(fval/caller._textProcess(child.attrib['div'],caller.types.int).toInt(caller))
                if 'add' in att and 'subtr' in att:
                    if att.index('add')<att.index('subtr'): # Multiplication before division
                        fval = int(fval+caller._textProcess(child.attrib['add'],caller.types.int).toInt(caller))
                        fval = int(fval-caller._textProcess(child.attrib['subtr'],caller.types.int).toInt(caller))
                    else:
                        fval = int(fval-caller._textProcess(child.attrib['subtr'],caller.types.int).toInt(caller))
                        fval = int(fval+caller._textProcess(child.attrib['add'],caller.types.int).toInt(caller))
                elif 'add' in att:
                    fval = int(fval+caller._textProcess(child.attrib['add'],caller.types.int).toInt(caller))
                elif 'subtr' in att:
                    fval = int(fval-caller._textProcess(child.attrib['subtr'],caller.types.int).toInt(caller))
                if to:
                    caller.varset(tv,caller.types.int(caller,str(fval)))
                else:
                    self.value = str(fval)
            def __init__(self,caller,val,const=False):
                self.vars['type'] = caller.types.type(caller,'int',True)
                self.value = val
                self.const = const
            def toInt(self,caller):
                return int(self.value)
            def isInt(val):
                pos = 0
                dot = False
                for i in val:
                    if dot:
                        if not i in ['0','1','2','3','4','5','6','7','8','9']:
                            return False
                    elif i == '-':
                        if pos != 0:
                            return False
                    elif i in ['0','1','2','3','4','5','6','7','8','9']:
                        pass
                    elif i == '.':
                        dot = True
                    else:
                        return False
                    pos += 1
                return True
            def make(caller, child):
                val = caller._textProcess(child.text).toString(caller)
                v = ''
                pos = 0
                dot = False
                for i in val:
                    if dot:
                        if not i in ['0','1','2','3','4','5','6','7','8','9']:
                            caller.error("TypeError",f"Illegal character in int: \"{i}\"")
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
                        if pos == 0:
                            v += str(ord(i))
                        else:
                            caller.error("TypeError",f"Illegal character in int: \"{i}\"")
                    pos += 1
                f = caller.types.int(caller,v,'const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def toString(self,caller):
                return self.value
            def equivto(self,caller,comp):
                if self.toString(caller)() == comp.toString(caller):
                    return True
                else:
                    return False
        class char(__type):
            typeName = "char"
            vars = {}
            def onCall(self,caller, child):
                print(self.value)
            def make(caller, child):
                f = caller.types.char(caller,caller._textProcess(child.text).toString(caller),'const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def __init__(self,caller,value,const=False):
                self.vars['type'] = caller.types.type(caller,'char',True)
                if caller.types.int.isInt(value):
                    self.value = chr(caller.types.int(caller,value).toInt(caller))
                else:
                    self.value = value[0]
                self.const = const
            def toString(self,caller):
                return self.value
            def toInt(self,caller):
                return ord(self.value)
            def equivto(self,caller,comp):
                if self.toString(caller)() == comp.toString(caller):
                    return True
                else:
                    return False
        class type(string):
            typeName = 'type'
        class bool(__type):
            typeName = "bool"
            vars = {}
            def onCall(self,caller, child):
                print('1' if self.value else '0')
            def make(caller, child):
                f = caller.types.bool(caller,child.text,'const' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def __init__(self,caller,value,const=False):
                self.vars['type'] = caller.types.type(caller,self.typeName,True)
                if value == '0':
                    self.value = False
                else:
                    self.value = True
                self.const = const
            def toString(self,caller):
                return '1' if self.value else '0'
            def toInt(self,caller):
                return 1 if self.value else 0
            def equivto(self,caller,comp):
                if self.toString(caller)() == comp.toString(caller):
                    return True
                else:
                    return False
        class ifblock(bool):
            typeName = 'ifblock'
        class cond(__type):
            typeName = "cond"
            vars = {}
            def __eval_children(self,caller,i,short,ormode=False):
                ret = []
                if i.tag == 'val':
                    thisbool = caller._textProcess(i.text,caller.types.bool)
                    if thisbool.value:
                        ret.append(True)
                    else:
                        ret.append(False)
                elif i.tag == 'equiv':
                    b = caller.is_equiv(caller._textProcess(i.attrib['v1']),caller._textProcess(i.attrib['v2']))
                    if b:
                        ret.append(True)
                    else:
                        ret.append(False)
                elif i.tag == 'not':
                    for x in i:
                        ret.append(not self.__eval_children(caller,x,short,ormode))
                elif i.tag == 'or':
                    v = []
                    for x in i:
                        v.append(self.__eval_children(caller,x,short,True))
                        if short:
                            for q in v:
                                if q:
                                    return True
                    app = False
                    for q in v:
                        if q:
                            ret.append(True)
                            app = True
                    if not app:
                        ret.append(False)
                elif i.tag == 'and':
                    v = []
                    for x in i:
                        v.append(self.__eval_children(caller,x,short,False))
                        if short:
                            for q in v:
                                if not q:
                                    return False
                    app = False
                    for q in v:
                        if not q:
                            ret.append(False)
                            app = True
                    if not app:
                        ret.append(True)
                else:
                    caller.run([i])
                for q in ret:
                    if not q:
                        return False
                return True
            def evaluate(self,caller):
                if not self.__static:
                    ret = []
                    for i in self.__children:
                        ret.append(self.__eval_children(caller,i,self.__short))
                        if self.__short:
                            for q in ret:
                                if not q:
                                    return False
                    for q in ret:
                        if not q:
                            return False
                    return True
                else:
                    return self.__children
            def onCall(self,caller, child):
                print('1' if self.evaluate(caller) else '0')
            def make(caller, child):
                f = caller.types.cond(caller,child,'const' in list(child.attrib.keys()),'static' in list(child.attrib.keys()),not 'long' in list(child.attrib.keys()))
                caller.varset(child.attrib['to'],f)
            def __init__(self,caller,children,const=False,static=False,short=True):
                self.__static = False
                self.const = const
                self.__short = short
                self.__children = children
                if static:
                    self.__children = self.evaluate(caller)
                self.__static = static
            def toString(self,caller):
                return '1' if self.evaluate(caller) else '0'
            def toInt(self,caller):
                return 1 if self.evaluate(caller) else 0
            def equivto(self,caller,comp):
                if self.toString(caller) == comp.toString(caller):
                    return True
                else:
                    return False
        types = {"funct":funct,"string":string,"null":null,"class":classType,'int':int,'char':char,'type':type,'bool':bool,'cond':cond,'ifblock':ifblock}
    def __init__(self,ET,langcall=False): # ET is the libary to load XML
        self.ET = ET
        self._globs = {}
        self._langcall = langcall
        self._autoglob = True
        self._locs = {}
        self._class = [self.types.null(self)]
        self._className = ""
        self._aSpec = 'public'
        self._retv = self.types.null(self)
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
    def _setClass(self,name,const,maketype,vars={},typeN='class'):
        if self._className == '':
            self._className = name
        else:
            self._className += '.'+name
        self._class.insert(0,self.types.classType(self,self._className,const,vars,maketype,typeN))
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
    def is_equiv(self,v1,v2):
        if v1.typeName == v2.typeName:
            return v1.equivto(self,v2)
        else:
            return v1.equivto(self,v2) #These do the same thing right now (just compare with tostring), but I want to add more in the future
    def varset(self,name,data,glob=False,overrideConst=False):
        if self._class[0].typeName != "null":
            self._class[0].vars[name] = data
        class vl:
            const = False
            typeName = 'null'
            vars = self._locs
            isClass = False
        s = name.split('.')
        for v in range(len(s)-1):
            i = s[v]
            if vl == 'psudotype':
                vl = self.types.type(self,'type',True)
            if i in vl.vars:
                if vl.isClass and vl.makeType == 'instance':
                    self.error("ClassError",f"Can not set value of instance class {vl.name} in {name}")
                vl = vl.vars[i]
                if vl.const:
                    self.error("DefineError",f"Name {i} is constant")
            else:
                self.error("DefineError",f"Name {i} is not defined in {name}")
        if vl == 'psudotype':
            vl = self.types.type(self,'type',True)
        if not overrideConst and s[-1] in list(vl.vars.keys()):
            if vl.vars[s[-1]].const:
                self.error("DefineError",f"Name {s[-1]} is constant")
        vl.vars[s[-1]] = data
        if self._autoglob or glob:
            class vl:
                typeName = 'null'
                vars = self._globs
            s = name.split('.')
            for v in range(len(s)-1):
                i = s[v]
                if vl == 'psudotype':
                    vl = self.types.type(self,'type',True)
                if i in vl.vars:
                    if vl.isClass and vl.makeType == 'instance':
                        return
                    vl = vl.vars[i]
                    if vl.const:
                        return
                else:
                    return
            if vl == 'psudotype':
                vl = self.types.type(self,'type',True)
            if not overrideConst and s[-1] in vl.vars:
                if vl.vars[s[-1]].const:
                    return
            vl.vars[s[-1]] = data
    def varget(self,name):
        class vl:
            typeName = 'null'
            vars = {}
            isClass = False
        for i,v in self._globs.items():
            vl.vars[i] = v
        for i,v in self._locs.items():
            vl.vars[i] = v
        for i in name.split('.'):
            if vl == 'psudotype':
                vl = self.types.type(self,'type',True)
            if i in vl.vars:
                if vl.isClass  and vl.makeType == 'instance':
                    self.error("ClassError",f"Can not get value of instance class {vl.name} in {name}")
                vl = vl.vars[i]
            else:
                self.error("DefineError",f"Name {i} is not defined in {name}")
        if vl == 'psudotype':
            vl = self.types.type(self,'type',True)
        return vl
    def varexists(self,name):
        class vl:
            vars = {}
        for i,v in self._globs.items():
            vl.vars[i] = v
        for i,v in self._locs.items():
            vl.vars[i] = v
        for i in name.split('.'):
            if vl == 'psudotype':
                vl = self.types.type(self,'type',True)
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
                text = text.replace(i[2]+'}',self.varget(i[3]).toString(self))
            v = re.finditer(r"\\(\{[ \n\t]*([^\} \n\t]*)[ \n\t]*\})",text)
            for i in v:
                text = text.replace(i[0],i[1])
            return cast(self,text)
    def _buildBuiltins(self):
        code = """<outer>
        <builtinvar-println><langcall command='println' text='{var: text}'> </langcall></builtinvar-println>
        <buildvar-builtin-current><langcall command='whereAmI-1' to='ret'> </langcall><return>{var: ret}</return></buildvar-builtin-current>
        <buildvar-builtin-textprocess><return>{var: data}</return></buildvar-builtin-textprocess>
        <buildvar-math-add><int to='v1'>{v1}</int><v1 add='{v2}' /><return>{var: v1}</return></buildvar-math-add>
        <buildvar-math-subtr><int to='v1'>{v1}</int><v1 subtr='{v2}' /><return>{var: v1}</return></buildvar-math-subtr>
        <buildvar-math-mult><int to='v1'>{v1}</int><v1 mult='{v2}' /><return>{var: v1}</return></buildvar-math-mult>
        <buildvar-math-div><int to='v1'>{v1}</int><v1 div='{v2}' /><return>{var: v1}</return></buildvar-math-div>
        <buildvar-math-exp><int to='v1'>{v1}</int><v1 exp='{v2}' /><return>{var: v1}</return></buildvar-math-exp>
        <buildvar-typeof><langcall command='typeof' to='ret'>{var: var}</langcall><return>{var: ret}</return></buildvar-typeof>
        <buildvar-userin><langcall command='userin' to='ret'> </langcall><return>{var:ret}</return></buildvar-userin>
        <builtinvar-print><langcall command='print' text='{var: text}'> </langcall></builtinvar-print>
        </outer>"""
        child = self.ET.fromstring(code)
        children = [i for i in child]
        f = self.types.funct(self,[i for i in children[0]],['text'],{},False,True,True)
        self.varset("println",f)
        cvars = {}
        cvars['current'] = self.types.funct(self,[i for i in children[1]],[],{},False,True)
        cvars['textprocess'] = self.types.funct(self,[i for i in children[2]],['data'],{},False,True)
        self.varset("builtins",self.types.classType(self,"builtins",True,cvars,'static'))
        cvars = {}
        cvars['add'] = self.types.funct(self,[i for i in children[3]],['v1','v2'],{},False,True)
        cvars['subtr'] = self.types.funct(self,[i for i in children[4]],['v1','v2'],{},False,True)
        cvars['mult'] = self.types.funct(self,[i for i in children[5]],['v1','v2'],{},False,True)
        cvars['div'] = self.types.funct(self,[i for i in children[6]],['v1','v2'],{},False,True)
        cvars['exp'] = self.types.funct(self,[i for i in children[7]],['v1','v2'],{},False,True)
        self.varset("math",self.types.classType(self,"math",True,cvars,'static'))
        f = self.types.funct(self,[i for i in children[8]],['var'],{},False,True,True)
        self.varset("typeof",f)
        f = self.types.funct(self,[i for i in children[9]],[],{},False,True,True)
        self.varset("userin",f)
        f = self.types.funct(self,[i for i in children[10]],['text'],{},False,True,True)
        self.varset("print",f)
    def _tag_langcall(self,child):
        if not self._langcall:
            self.error("LangCallError","Current funct does not have langcall permissions")
        elif child.attrib['command'] == 'println':
            print(self._textProcess(child.attrib['text']).toString(self))
        elif child.attrib['command'] == 'print':
            print(self._textProcess(child.attrib['text']).toString(self),end='')
        elif child.attrib['command'] == 'rawvarprint':
            print(vars(self.varget(child.attrib['name'])))
        elif child.attrib['command'] == 'printvars':
            print("Locs: "+str(self._locs))
            print("Globs: "+str(self._globs))
        elif child.attrib['command'] == 'whereAmI':
            self.varset(child.attrib['to'],self.types.string(self,self._cPath,False))
        elif child.attrib['command'] == 'whereAmI-1':
            v = self._cPath[::-1].replace(self._cPath.split(",")[-1][::-1]+',',"",1)[::-1]
            #v = v[::-1].replace(v.split(",")[-1][::-1]+',',"",1)[::-1]
            self.varset(child.attrib['to'],self.types.string(self,v,False))
        elif child.attrib['command'] == 'typeof':
            self.varset(child.attrib['to'],self.types.type(self,self._textProcess(child.text).typeName,False))
        elif child.attrib['command'] == 'userin':
            self.varset(child.attrib['to'],self.types.string(self,input(),False))
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
    def _tag_if(self,child):
        run = self._textProcess(child.attrib['cond'],self.types.cond).evaluate(self)
        if run:
            self.run(child)
        if 'block' in list(child.attrib.keys()):
            self.varset(child.attrib['block'],self.types.ifblock(self,'1' if run else '0'),False)
    def _tag_ifn(self,child):
        run = self._textProcess(child.attrib['cond'],self.types.cond).evaluate(self)
        if not run:
            self.run(child)
        if 'block' in list(child.attrib.keys()):
            self.varset(child.attrib['block'],self.types.ifblock(self,'0' if run else '1'),False)
    def _tag_elseif(self,child):
        if not self.varexists(child.attrib['block']):
            self.error("IfError",f"Block variable {child.attrib['block']} does not exist")
        block = self.varget(child.attrib['block'])
        if block.typeName != 'ifblock' and block.typeName != 'bool':
            self.error("IfError","Invalid type for block")
        if not block.value:
            run = self._textProcess(child.attrib['cond'],self.types.cond).evaluate(self)
            if run:
                self.run(child)
            self.varset(child.attrib['block'],self.types.ifblock(self,'1' if run else '0'),False)
    def _tag_elseifn(self,child):
        if not self.varexists(child.attrib['block']):
            self.error("IfError",f"Block variable {child.attrib['block']} does not exist")
        block = self.varget(child.attrib['block'])
        if block.typeName != 'ifblock' and block.typeName != 'bool':
            self.error("IfError","Invalid type for block")
        if not block.value:
            run = self._textProcess(child.attrib['cond'],self.types.cond).evaluate(self)
            if not run:
                self.run(child)
            self.varset(child.attrib['block'],self.types.ifblock(self,'0' if run else '1'),False)
    def _tag_else(self,child):
        if not self.varexists(child.attrib['block']):
            self.error("IfError",f"Block variable {child.attrib['block']} does not exist")
        block = self.varget(child.attrib['block'])
        if block.typeName != 'ifblock' and block.typeName != 'bool':
            self.error("IfError","Invalid type for block")
        if not block.value:
            self.run(child)
            self.varset(child.attrib['block'],self.types.ifblock(self,'1'),False)
    def _tag_while(self,child):
        run = self._textProcess(child.attrib['cond'],self.types.cond).evaluate(self)
        while run:
            self.run(child)
            run = self._textProcess(child.attrib['cond'],self.types.cond).evaluate(self)
    def _tag_whilen(self,child):
        run = self._textProcess(child.attrib['cond'],self.types.cond).evaluate(self)
        while not run:
            self.run(child)
            run = self._textProcess(child.attrib['cond'],self.types.cond).evaluate(self)
    _tags = {'langcall':{'f':_tag_langcall,'reqattrib':["command"],'optattrib':None,'takesChildren':True},'public':{"f":_tag_public,"reqattrib":[],"optattrib":[],'takesChildren':True},'return':{'f':_tag_return,'reqattrib':[],'optattrib':[],'takesChildren':True},'if':{'f':_tag_if,'reqattrib':['cond'],'optattrib':['block'],'takesChildren':True},'ifn':{'f':_tag_ifn,'reqattrib':['cond'],'optattrib':['block'],'takesChildren':True},'elseif':{'f':_tag_elseif,'reqattrib':['cond','block'],'optattrib':[],'takesChildren':True},'elseifn':{'f':_tag_elseifn,'reqattrib':['cond','block'],'optattrib':[],'takesChildren':True},'else':{'f':_tag_else,'reqattrib':['block'],'optattrib':[],'takesChildren':True},'while':{'f':_tag_while,'reqattrib':['cond'],'optattrib':[],'takesChildren':True},'whilen':{'f':_tag_whilen,'reqattrib':['cond'],'optattrib':[],'takesChildren':True}} #Optattrib=None is equiv to **kwargs
