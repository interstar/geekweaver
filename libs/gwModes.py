# Released under the GNU General Public License, v3.0 or later
# Copyright (c) 2007 Phil Jones <interstar@gmail.com>


# OPML to website

from opml import *
from os import removedirs, mkdir, rmdir, getcwd, makedirs
from shutil import copyfile, copytree

import re
from string import Template
from sys import *

import csv
from UniCsv import UnicodeReader

from gwNode import *
from SymbolTable import *
from logger import *
from gwHelpers import *

# functions


# classes        


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
    return ArgBlock(GWNode(''),UrMode(), nullFellowTraveller() ,Logger())

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
        

class UrMode :

    """
    A Mode is something within which we interpret the syntax of a Node.
    Different modes *can* interpret the same syntax in different ways (although it's generally not encouraged)
    The most obvious (and useful) difference is between SiteMode and various in-page modes
    In SiteMode, nodes without any further syntax get turned into subdirectories in the file system. In
    in-page modes they are text that goes into the page.
    The UrMode class is the parent of all other modes. It's EvalNode routine supports the fundamental stuff
    in GeekWeaver like defining and calling re-usable blocks, commenting, and calling into Python.
    You really shouldn't over-ride this in a mode subclass unless you want to change this fundamental behaviour

    Instead use modeEvalNode for the stuff which is specific to your mode if you define a new one.    
    """

    def __init__(self, environment) :
        self.environment = environment

    def log(self,s, typ='normal') :
        self.environment.interpreter.log(s,typ)

    def getLog(self) :
        return self.environment.logger

    def getFromSymbolTable(self, sym) :
        return self.environment.symbolTable.get(sym)
    
    def pushFrameToSymbolTable(self, frame) :
        self.environment.symbolTable.pushFrame(frame)

    def popFrameFromSymbolTable(self) :
        self.environment.symbolTable.popFrame()

    def getMode(self,s) :
        return self.environment.interpreter.modes[s]

    def makeArgBlock(self, node, evalSymbols = lambda x : x) :
        return ArgBlock(node, self, nullFellowTraveller(), Logger())
    
    def makeEvalClosure(self, fellow) :
        """ This factory makes a closure for calling the local evalNode """
        def g(node, mode, wrap=nullFunc) :
            return mode.eval(x,fellow.inc())

    def sJoin(self, a) :
        return ''.join(a)

    def jFact(self, fellow) :
        """
        jFact makes a closure that joins all the children of a node together.
        
        If all the children evaluate to strings, then join the strings into one
        otherwise, return a list of strings and nodes, but join as many strings as
        possible
        """
        
        def g(node, head='', wrap=nullFunc) :
            a = [wrap(self.evalNode(x, fellow.inc())) for x in node.children]
            return head + self.sJoin(a)
        return g

    def callBlock(self,node, s, fellow, args=[]) :
        joinChildren = self.jFact(fellow)

        # we're dereferencing a symbol, so get it from the symbol table *before* putting new args in
        c = self.getFromSymbolTable(s)

        # put args of this call (ie. children of the tree node) into the symbolTable
        blocks = ArgBlock(node,self,fellow,self.environment.logger)

        self.log("callBlock %s (line args : %s)" % (s,args))        
        
        return c.call(blocks, self, fellow)
                       

    def evalNode(self, node, fellow) :
        joinChildren = self.jFact(fellow)
        self.log('evalNode %s ' % (node.text))
        fellow.sideFx(node,fellow)
        if node.__class__ == GWNode :
            # the node is a sub-tree
            s = self.evalSymbols(node.text,fellow)
          
            # General Structural Syntax
            
            if re.match('::',s) :
                # we're defining a block
                s = s[2:]
                self.log('defining block : %s'%s)
                if s.find('@') >= 1 :
                    # block from template file
                    xs = [x.strip() for x in s.split('@')]
                    self.log('block defined from file : %s' % xs[1])
                    b = fromFile(xs[1], self.getLog(),'')
                    self.pushFrameToSymbolTable({xs[0] : CTemplate(xs[0],b)})
                elif s.find('<') >= 1 :
                    # load a subtree from another opml file
                    xs = [x.strip() for x in s.split('<')]
                    self.log('block defined from subtree in file : %s' % xs[1])
                    self.pushFrameToSymbolTable({xs[0] : CTemplate(xs[0],self.environment.interpreter.opmlFileToTree(xs[1]))})
                    
                else :
                    # we're defining a subtree
                    # put it into the table, no cute lexical closures yet
                    self.pushFrameToSymbolTable({s.strip() : CBlock(s.strip(),node)})
                return ''                    

            if re.match('&&data',s) :
                self.log('Mode transition to data-mode')                
                m = self.environment.interpreter.modes['data']
                fakester = GWNode('')
                fakester.children = node.children
                return fakester
            
            if re.match('&&',s) :
                modeName = s[2:].strip()
                self.log('Mode transition to %s' % modeName)
                m = self.environment.interpreter.modes[modeName]
                blocks = [m.evalNode(x, fellow) for x in node.children]
                return self.sJoin(blocks)                                                   

            if re.match(':for',s) :
                ll = LexLine(s,':')
                self.log("In :for")
                localName = ll.args[0]
                argBlock = ll.args[1]
                if argBlock[0] == '#' : # it's just syntax to help read, more than anything else
                    argBlock = argBlock[1:]
            
                a = self.getFromSymbolTable(argBlock) # the arg block
                blocks = []
                for x in a.children:
                    self.environment.getSymbolTable().pushFrame( {localName : x} )
                    self.log("%s is bound to %s" % (localName,x))
                    blocks.append(self.sJoin( [self.evalNode(y, fellow) for y in node.children]))
                    self.environment.getSymbolTable().popFrame()
                    
                return self.sJoin(blocks)
                
            
            if re.match(':\*',s) :
                # call a block on each item of the sublist (kind of a comprehension)
                blocks = []
                blockName = s[2:].strip()
                self.log('List Comprehension (applying block : %s to all items in list)' % s)
                for x in node.children :
                    args = re.split('\s',x.text)
                    blocks.append(self.callBlock(x,blockName,fellow, args))
                return self.sJoin(blocks)

            if re.match(':',s) :
                self.log('Block call : %s' % s)
                ll = LexLine(s,':')
                return self.callBlock(node,ll.key,fellow, ll.args)
            
            if re.match('!',s) :
                # it's a python call (another dangerous thing)
                return eval(s[1:])                

            if re.match('//',s) :
                # this node and sub-tree commented out
                return ''
            
            # If we got here then the line was neither defining a block, calling a block, nor calling a bit of python
            return self.modeEvalNode(node, fellow)

        
        else :
            # the nood is actually a string so we just evaluate any symbols in it and return it
            return self.evalSymbols(node,fellow)

    def modeEvalNode(self, node, fellow) :
        # this method likely to be over-ridden in the sub-classes
        # right now, because we don't have more specific information
        # we'll just create a string from the text and evaluating the children
        s = self.evalSymbols(node.text,fellow)
        return  s + self.sJoin([self.evalNode(x,fellow) for x in node.children]) 

    def stringEval(self,node,environment) :
        # here we're going for a radical change :
        # only now we flatten everything to a string
        s = self.evalSymbols(node.text,fellow)
        return  s + self.sJoin([self.stringEval(x,environment) for x in node.children]) 

    def symbolAsString(self, sym, fellow) :
        v = self.getFromSymbolTable(sym)

        s = ''
        if isNode(v) :
            s = v.text
            for x in v.children :
                sv = self.evalNode(x,fellow)
                if isStr(sv) :
                    s = s + sv
                elif isNode(sv) :
                    s = s + sv.text
                else :
                    s = s + '%s' % sv
            return s
        else :
            return v
            
            
        
    def evalSymbols(self, s, fellow) :
        self.log('evalSymbols with %s' % s)

        if re.match('#',s) :
            sym = s[1:].strip()
            return self.getFromSymbolTable(sym)
            
        if s.find('$') >= 0 :

            d = {} # dictionary into which we'll put all symbols

            if re.search('\[',s) >= 0 :
                # this handles vars which are actually indexes within the children,
                # (like list index)
                r = re.compile(r'\$(?P<name>[A-Za-z0-9_]+)\[(?P<index>[0-9\.]+)\]')
                ds = r.findall(s)
                for m in ds :
                    sym = m[0]
                    i = m[1]
                    
                    try :
                        a = self.getFromSymbolTable(sym)
                        if isNode(a) :
                            if re.match('\.',i) :
                                v = a.text
                                s = r.sub(v,s,1)
                            else :
                                try :
                                    i = int(i)
                                    v = self.evalNode(a.children[int(i)],fellow)
                                except :
                                    v = "ERROR : %s is not a valid index" % i
                            s = r.sub(v,s,1)
                        else :
                            v = "ERROR : %s is not a node you can look for subscript %s of" %(a,i)
                            s = r.sub(v,s,1)
                    except Exception, e:
                        v = "ERROR : can't find symbol %s (%s)" % (sym,e)
                        s = r.sub(v,s,1)
                    
            if s.find('$/') >= 0 :
                # this handles the vars with default values
                r = re.compile(r'\$\/(?P<name>[A-Za-z0-9_]+)\/(?P<default>\S*)\/')
                ds = r.findall(s)
                for m in ds :
                    try :
                        vm = self.symbolAsString(m[0], fellow)
                        s = r.sub('$\g<name>',s)
                        d[m[0]] = vm
                    except :
                        s = r.sub('\g<default>',s)
                
            r = re.compile(r'\$([A-Za-z0-9_]+)')
            ms = r.findall(s)
            r = re.compile(r'\$\{([A-Za-z0-9_\s]+)\}')
            ms = ms + r.findall(s)
            for m in ms :
                try :
                    d[m] = self.symbolAsString(m,fellow)
                except : pass
            return Template(s).safe_substitute(d)
        else :
            return s

    
class PrimalMode(UrMode) :

    """
    This is the mode that we start in, outside SiteMode
    """
    
    def modeEvalNode(self, node, fellow) :
        
        s = self.evalSymbols(node.text,fellow)  
        self.log('evalPrimalNode %s' % s)
        if re.match('@index',s) :
            # define template file
            self.log('evalPrimalNode\defining index template')
            fName = s[6:].strip()
            self.environment.interpreter.indexTemplate = Template(fromFile(fName,self.getLog(),''))

        elif re.match('@fileExt',s) :
            # define default output file extension
            self.log('evalPrimalNode\defining default file extension')
            ext = s[8:].strip()
            self.environment.interpreter.defaultFileExtension = ext

        elif re.match('@root',s) :
            # define default output file extension
            self.log('evalPrimalNode\defining (coded) siteRoot')
            r = s[5:].strip()
            self.environment.interpreter.codedSiteRoot = r
            
        elif s[0] == '&' :
            # from primal, this is starting the site
            self.log('starting site')
            self.log('make siteMap')
            self.log('cDir is %s' % fellow.cDir)
            self.log('root is %s' % self.environment.siteRoot())
            self.environment.siteMap = self.environment.interpreter.makeSiteMap(node, fellow.cDir)
            self.log('finish starting a site')
            return self.getMode('staticSite').evalNode(node, (fellow.inc()).newDir(self.environment.interpreter.dName))

        return self.sJoin([self.evalNode(x,fellow.inc()) for x in node.children])


        
class StaticSiteMode(UrMode) :

    def modeEvalNode(self, node, fellow) :
        s = self.evalSymbols(node.text,fellow)  
        self.log('evalSiteNode : %s ' % s)
        nd = fellow.cDir
            
        if '>'.find(s[0]) > -1 :
            self.log('evalSiteNode\doing nothing with %s' % s[0])

        elif re.match('@cDir',s) :
            nd = fellow.cDir + '/' + spaceUnder(s[5:].strip())
            self.log('evalSiteNode\changing the cDir to %s' % nd)

        else :
            if s[0] == '&'  : s = s[1:]
            nd = fellow.cDir + '/' + spaceUnder(s)
            self.log('evalSiteNode\creating directory %s (cDir %s)' % (nd, fellow.cDir))
            makedirs(nd)
            self.log('evalSiteNode\adding to siteMap %s ' % nd)
                     
        index = []
        self.log('evalSiteNode\starting index loop')
        for x in node.children :
            self
            if x.text == '' :
                pass
            elif x.text[0] == '&' :
                lpn = self.processPage(x, (fellow.inc()).newDir(nd))
                i = [lpn.pageName,spaceUnder(lpn.outFileName),False]
                index.append(i)
                self.log('index += %s'%i)

            elif x.text[0] == ':' :
                self.log('eval block from StaticSiteMode')
                self.evalNode(x, fellow)
            
            elif re.match('>\s*(.+)>\s*(\S+)',x.text) :
                m = re.match('>\s*(.+)\s*>\s*(\S+)',x.text)
                linkText = (m.groups(0)[0]).strip()
                dest = m.groups(0)[1]
                index.append([linkText,dest,False])

            else :
                self.evalNode(x, (fellow.inc()).newDir(nd))
                index.append([x.text,spaceUnder(x.text)+'/index.html',True])                    

        self.environment.interpreter.indexPage(node.text, index, fellow.newDir(nd))

        return ''

    def processPage(self, node, fellow) :
        # now we're inside a page beause we hit a &
        fellow.sideFx(node,fellow)
        paras = []
        text = self.evalSymbols(node.text,fellow)
        self.log('processPage : node.text is %s ' % text)
        lpn = LexPageName(text,self.environment.interpreter.defaultFileExtension)
        
        if lpn.matches == True :
            self.environment.currentPageName = lpn.pageName
            if lpn.symbol != '' :
                page = self.getMode('html').callBlock(node, lpn.symbol, fellow)                             
            else :
                paras = [self.getMode('html').evalNode(x, fellow) for x in node.children ]
                page = self.sJoin(paras)
       
        self.environment.siteMapper.add(fellow.cDir,spaceUnder(lpn.outFileName),spaceUnder(lpn.outFileName),page.encode('utf-8'))

        return lpn


class HtmlMode(UrMode) :

    def patternReplace(self,t) :
        if re.search(r'\[\[(\S+)\s*(\S+)\]\]',t) :
            t = re.sub(r'(\[\[(?P<url>\S+)\s*(?P<text>\S+)\]\])',"<a href='" + self.environment.siteRoot() + "\g<url>'>\g<text></a>",t)
        return t


    def modeEvalNode(self, node, fellow) :
        b = []
        t = self.evalSymbols(node.text,fellow)
        joinChildren = self.jFact(fellow)

        t = self.patternReplace(t)
        
        if len(t) > 0 :
            
            if t[0] == '=' :
                b.append('<h2>%s</h2>' % (t[1:]).strip())
                b.append( joinChildren(node))

            elif re.match('\.<(.+)>',t) :
                m = re.match('\.<(.+)>',t)        
                b.append("""<%s>"""  % m.groups()[0] )
                b.append( joinChildren(node))

                i = m.groups()[0].find(' ')
                if i < 0 :
                    b.append('</%s>' % m.groups()[0] )
                else :
                    b.append('</%s>' % m.groups()[0][0:i] )


            elif t[0] == '.' :
                ll = LexLine(t,'.')
                b.append("""<div class='%s'>%s"""  % (ll.key,' '.join(ll.args)))
                b.append( joinChildren(node))
                b.append('</div>')

            elif t[0] == ';' :
                ll= LexLine(t,';')
                b.append("""<div id='%s'>%s"""  % (ll.key,' '.join(ll.args)))
                b.append( joinChildren(node))
                b.append('</div>')


            elif re.match(':csv',t) :
                
                ll = LexLine(t,":csv")
                fName = ll.args[0].strip()
                if ll.args != [] :
                    delim = ll.args[1].strip()
                else :
                    delim = ','                  
                
                self.log('opening external CSV file %s and delim is *%s* ' % (fName,delim))
                reader = UnicodeReader(open(fName, "rb"),csv.excel,'unicode_escape',delimiter=delim.encode('utf-8'))
                csvNode = GWNode('')
                self.log('Got reader. Starting to iterate through it')
                for row in reader :
                    self.log('row : %s' % row)
                    r = GWNode('')
                    for c in row :
                        self.log('adding cell %s' % c.text)
                        r.addChild(GWNode(c))
                    csvNode.addChild(r)
                self.log('YYYY %s'% csvNode)
                return csvNode

            elif t[0] == '@' :
                tpl = Template(fromFile(t[1:],self.getLog(),''))
                blocks = self.evalArgChildren(node,joinChildren)
                b.append(tpl.safe_substitute(blocks))

            elif re.match(r'\?\s*([A-Za-z]+)\s*->\s(\S+)',t) :
                m = re.match(r'\?\s*([A-Za-z]+)\s*->\s(\S+)',t)
                b.append("<form name='%s' method='GET' action='%s'>" % (m.groups(0)[0],m.groups(0)[1]))
                for child in node.children :
                    b.append(self.getMode('htmlForm').evalNode(child, fellow))
                b.append("\n</form>")

            elif re.match(r'\?\s*([A-Za-z]+)\s*=>\s(\S+)',t) :
                m = re.match(r'\?\s*([A-Za-z]+)\s*=>\s(\S+)',t)
                b.append("<form name='%s' method='POST' action='%s'>" % (m.groups(0)[0],m.groups(0)[1]))
                for child in node.children :
                    b.append(self.getMode('htmlForm').evalNode(child, fellow))
                b.append("\n</form>")

            elif re.match(r'>\s*(.+)\s*>\s*((\S+))',t) :
                m = re.match(r'>\s*(.+)\s*>\s*((\S+))',t)
                b.append("<a href='%s'>%s</a>" % (m.groups(0)[1],m.groups(0)[0].strip()))

            elif t[0] == ']':
                ll = LexLine(t,']')
                b.append("<img src='%s' alt='%s'/>" % (ll.key,' '.join(ll.args)))

            elif t[0] == '*' :
                ll = LexLine(t,'*')
                b.append("""<ul class='%s'>""" % ll.key)
                jc = self.jFact(fellow)
                b.append( jc(node, '', lambda x : '\n<li>%s</li>' % x) )
                b.append('</ul>')
                
            else :
                b.append(t)
                b.append( joinChildren(node))
        else :
            # text value of this node is empty but children may still have value
            b.append(t)
            b.append( joinChildren(node))
            
        return self.sJoin(b)


class HtmlFormMode(HtmlMode) :

    def modeEvalNode(self, node, fellow) :
        s = self.evalSymbols(node.text,fellow).strip()
        self.log('HtmlFormMode modeEvalNode : %s' % s)

        if re.match(r'\?\?',s) :
            s = s[2:]
            if s.find(':') > 0 :
                parts = s.split(':')
                return "\n%s : <input name='%s'/>"  % (parts[0],parts[1])
            else :
                return "\n<input name='%s'/>" % s
        elif re.match(r'\?\*',s) :
            b = []
            b.append("\n<select name='%s'>" % s[2:])
            for x in node.children :
                parts = [y.strip() for y in self.evalSymbols(x.text,fellow).split(':')]
                b.append("\n<option value='%s'>%s</option>" % (parts[0], parts[1]))
            b.append("\n</select>")
            return self.sJoin(b)
        elif re.match(r'\?_',s):
            s = s[2:]
            if s.find(':') > 0 :
                parts = s.split(':')
                return """
%s : <textarea name='%s'>
</textarea>""" % (parts[0].strip(),parts[1].strip())
            else :
                return """
<textarea name='%s'>
</textarea>""" % s.strip()
        elif re.match(r'\[\]',s) :
            return "\n<input type='submit'/>"
        elif re.match(r'\[\s*([A-Za-z ]+)\s*\]',s) :
            m = re.match(r'\[\s*([A-Za-z ]+)\s*\]',s)
            return "\n<input value='%s' type='submit'/>" % m.groups(0)
        
        elif re.match(r'\[\s*([A-Za-z]+)\s*;\s*([A-Za-z]+)\s*\]',s) :
            m = re.match(r'\[\s*([A-Za-z]+)\s*;\s*([A-Za-z]+)\s*\]',s)
            return "\n<input value='%s' name='%s' type='button'/>" % (m.groups(0)[0], m.groups(0)[1])
        
        return HtmlMode.modeEvalNode(self, node, fellow)

class PhpMode(HtmlMode) :

    def subPercent(self, s) :
        r = re.compile(r'\%([A-Za-z]+)')
        return r.sub(r'<? echo $\1 ?>',s)
        
    def modeEvalNode(self, node, fellow) :
        s = self.evalSymbols(node.text,fellow).strip()
        joinChildren = self.jFact(fellow)
        
        self.log('PHPMode modeEvalNode : "%s"' % s)

        if s == '' : return ''
        
        if s[0] == '=' :
            var = s[1:].strip()
            return "<? $%s = $HTTP_GET_VARS['%s']; ?>" % (var,var)
        
        if re.match('\?:',s) :
            # cond in PHP
            build = []
            if len(node.children) == 0 :
                return ''
            i = 1
            build.append("""<? if %s {
%s
}""" % (node.children[0].text, node.children[0].children[0].text))
            if len(node.children) == 1 :
                build.append(' ?>')
                return self.sJoin(build)
            
            while len(node.children) - 1 > i :
                build.append(""" elseif %s {
%s
}""" % (node.children[i].text, self.evalNode(node.children[i].children[0], fellow)))
                i=i+1
            build.append(""" else {
%s
} ?>""" % (self.evalNode(node.children[i].children[0], fellow)))
            return self.sJoin(build)

        if re.match('"""',s) :
            return """echo '%s';""" % joinChildren(node)
        
        s = HtmlMode.modeEvalNode(self, node, fellow)
        return self.subPercent(s)


class JavascriptMode(UrMode) :

    """
    Right now, the Javascript mode does nothing but put some useful newlines.
    We may find decide on some other short-hands later
    """
    def modeEvalNode(self, node,  fellow) :
        s = self.evalSymbols(node.text,fellow)
        joinChildren = self.jFact(fellow)
        b = []

        if len(s) > 0 :

            if '{;}'.find(s[-1]) >= 0 :
                b.append(s + '\n')
                
            else :
                b.append(s)

            b.append( joinChildren(node))
        else :
            # text value of this node is empty but children may still have value
            b.append(s)
            b.append( joinChildren(node))
            
        return self.sJoin(b)



class DataMode(UrMode) :
    """
    DataMode is a little bit different from all the others. It acts rather like the quote in Lisp
    in that it returns the sub-trees, unflattened into strings.
    Careful, because not everything knows what to do with data.
    Really, only functions that are expecting it should be given data.
    """
    def modeEvalNode(self,node,fellow) :
        return node

    def sJoin(self, a) :
        return a

    def jFact(self, fellow) :
        """
        jFact makes a closure that joins all the children of a node together.
        
        If all the children evaluate to strings, then join the strings into one
        otherwise, return a list of strings and nodes, but join as many strings as
        possible
        """
        
        def g(node, wrap=nullFunc) :
            a = [wrap(self.evalNode(x, fellow.inc())) for x in node.children]
            return a
        return g
        
