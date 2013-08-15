# Released under the GNU General Public License, v3.0 or later
# Copyright (c) 2007 Phil Jones <interstar@gmail.com>

# OPML to website

from opml import *

import re
from string import Template
from sys import *

import csv
from UniCsv import UnicodeReader

from gwNode import *
from SymbolTable import *
from logger import *
from gwHelpers import *

from blocks import *

try :
    from markdown import markdown 
    MARKDOWN_ENABLED = True
except e : 
    MARKDOWN_ENABLED = False


# functions


# classes        

class BaseMode :

    """
    A Mode is something within which we interpret the syntax of a Node.
    Different modes *can* interpret the same syntax in different ways (although it's generally not encouraged)
    The most obvious (and useful) difference is between SiteMode and various in-page modes
    In SiteMode, nodes without any further syntax get turned into subdirectories in the file system. In
    in-page modes they are text that goes into the page.
    The BaseMode class is the parent of all other modes. It's EvalNode routine supports the fundamental stuff
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

            if re.match(':log',s) :
                self.log(s[4:],'program')
                blocks = [self.evalNode(x, fellow) for x in node.children]
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
            # the node is actually a string so we just evaluate any symbols in it and return it
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
        self.log('evalSymbols with *%s*' % s)

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


class PlainTextMode(BaseMode) :
    """
    A simple text mode. Joins every list item into CR separated lines.
    """
    def sJoin(self, a) :
        return '\n'.join(a)

    def modeEvalNode(self, node, fellow) :    
        s = self.evalSymbols(node.text,fellow)
        s = s + "\n" + self.sJoin([self.evalNode(x,fellow) for x in node.children])
        return s
        

class DataMode(BaseMode) :
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
        
class MarkdownMode(BaseMode) :
    def sJoin(self, a) :
        return '\n'.join(a)

    def modeEvalNode(self, node, fellow) :
        s = self.evalSymbols(node.text,fellow) 
        m = self.environment.interpreter.modes["plaintext"]        
        blocks = [m.evalNode(x, fellow) for x in node.children]
        s = s + "\n" + self.sJoin(blocks)
        
        self.log(s,'pre')
        if MARKDOWN_ENABLED :
            s = markdown(s)
        else :
            self.log("Markdown was invoked, but you don't have the library installed for Python on your machine")
            
        self.log(s,'html')
        return s        
