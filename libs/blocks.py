import re
from gwNode import GWNode
from string import Template

# Classes
class ArgBlock(dict) :

    """
    when a node is interpreted as an ArgBlock we find all the ways it contains arguments that
    can be passed to a block
    - lineArgs are ,, separated args on the initial line of the call and are mapped to $_0, $_1 etc.
    - namedChildren are the children defined with
      name : val
      and are mapped to $name 
    - anonChildren which are strings are child nodes without :
      and are mapped to $__0 , $__1 , $__2   etc.
    - anonChildren which are data are mapped to 
    There are also three lists : lineArgs, namedChildren, anonChildren so we can iterate through these groups
    """

    def getValOfArg(self, s) :
        if s[0] != '#' :
            return s
        else :
            return self.mode.getFromSymbolTable(s[1:])
            
            
    def setLineArgs(self, node) :
        
        if re.match('\S+\s+(.+)',node.text) :
            # something on the command line, at least one arg
            s = (re.match('\S+\s+(.+)',node.text)).groups()[0]

            lineNode = GWNode('')
           
            if s.find(',,') < 0 :
                # only one arg,
                v = self.getValOfArg(s.strip())
                self.lineArgs = [v]
                self['_0'] = v
                lineNode.children.append(GWNode(v))
            else :
                self.lineArgs = [self.getValOfArg(x.strip()) for x in s.split(',,')]
                for x in range(len(self.lineArgs)) :
                    self['_%s'%x] = self.lineArgs[x]
                    lineNode.children.append(GWNode(self.lineArgs[x]))
            self['_'] = lineNode


    def setChildArgs(self, node, mode, fellow) :
        
        for child in node.children :
            t = mode.evalSymbols(child.text,fellow)
                
            if t.find(':') > 0 :
                # we are always going to eval the argument as a string here                
                parts = t.split(':')
                key = parts[0].strip()

                # it's all strings 
                joinChildren = mode.jFact(fellow)
                val = joinChildren(child, parts[1].strip())

                self.namedChildren.append(val)
                self[key] = val

            elif t.find('#') > 0 :
                # this is a data arg
                parts = t.split('#')
                key = parts[0].strip()

                # ok, we've got just one data node under this key, so we're going to produce a dummy
                val = GWNode('')
                val.children = child.children

                self.namedChildren.append(val)
                self[key] = val
                    
            else :
                # this is going to be an anon arg (always treat as a string)
                val = mode.evalNode(child,fellow)
                self.anonChildren.append(val)

        self['__'] = GWNode('')
        for x in range(len(self.anonChildren)) :
            self['__%s'%x] = self.anonChildren[x]
            self['__'].children.append(GWNode(self.anonChildren[x]))



    
    def __init__(self, node, mode, fellow, log) :
        self.lineArgs = []
        self.namedChildren = []
        self.anonChildren = []
        self.log = log
        self.setLineArgs(node)
        self.setChildArgs(node, mode, fellow)


    def getAnonChildren(self) : return self.anonChildren
    
def nullArgBlock() :
    return ArgBlock(GWNode(''),BaseMode(), nullFellowTraveller() ,Logger())

class CBlock :
    """
    Callable Block (use it as a function)
    """

    def __init__(self, name, tree, frame={}) :
        self.name = name
        self.body = tree
        self.frame = frame # we'll make this a closure in the future

    def call(self, argBlock, mode, fellow) :
        mode.pushFrameToSymbolTable(argBlock)
        mode.log('Pushed to SymbolTable')
        mode.log(mode.environment.symbolTable,'symTable')

        joinChildren = mode.jFact(fellow)
        rVal = joinChildren(self.body)            

        mode.popFrameFromSymbolTable()
        mode.log('Pop From SymbolTable')
        mode.log(mode.environment.symbolTable,'symTable')
        mode.log('return value (rVal) is %s' % rVal)
        
        return rVal

class CTemplate :
    """
    Callable Template
    """

    def __init__(self, name, tString, frame={}) :
        self.name = name
        self.body = tString
        self.frame = frame

        
    def call(self, argBlock, mode, fellow) :
        mode.pushFrameToSymbolTable(argBlock)
        mode.log('Pushed to SymbolTable')
        mode.log(mode.environment.symbolTable,'symTable')
        
        tpl = Template(mode.evalSymbols(self.body,fellow))
        rVal = tpl.safe_substitute(argBlock)

        mode.popFrameFromSymbolTable()
        mode.log('Pop From SymbolTable')
        mode.log(mode.environment.symbolTable,'symTable')
        mode.log('return value (rVal) is %s' % rVal)
        
        return rVal

