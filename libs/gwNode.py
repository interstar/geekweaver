# Released under the GNU Lesser General Public License, v2.1 or later
# Copyright (c) 2007 Phil Jones <interstar@gmail.com>

""" This is what GeekWeaver trees are build of"""
from xml.dom.minidom import parse, parseString
import re

def isStr(x) :
    return x.__class__ == str

def isNode(x) :
    return x.__class__ == GWNode

def isList(x) :
    return x.__class__ == list

def isNull(x) :
    if isStr(x) : return x == ''
    if isNode(x) : return x.text == '' and x.children == []
    if isList(x) : return x == []
    return False


class GWNode :
    """This is the node that the AST of our program is made of"""
    
    def __init__(self, text='') :
        self.text = text
        self.children = []

    def addChild(self, tNode) :
        if tNode.__class__ == str :
            self.children.append(GWNode(tNode))
        else:
            self.children.append(tNode)
        return self

    def size(self,t) :
        return 1 + sum([self.size(x) for x in t.children])

    def textMatch(self, s) :
        return re.match(s,self.text)

    def matches(self,s) :
        return self.textMatch(s) != None

    def stringEval(self, mode, environment) :
        return mode.stringEval(self,environent)

class LexLine :
    """
    This class used to break up and represent a line (s) into
        matches?  (true or false if the pattern matches)
        glyph (what's the initial symbol on the front)
        keyword (which optionally breaks into)
            class
            id
        arglist
    """

    def keyword(self, s) :
        self.key = s
        if s.find(';') > 0 :
            parts = s.split(';')
            self.cls = parts[0]
            self.id = parts[1]
        else :
            self.cls = s
            self.id = ''
            
    def __init__(self,s,glyph) :
        self.args = []
        self.cls = ''
        self.id = ''
        self.key = ''
        self.matches = False
        self.s = s

        if s[0:len(glyph)] == glyph :
            self.matches = True
            s = s[len(glyph):].strip()
            if re.match('\S+\s+\S',s) :
                #has keyword and arg
                parts = s.split(' ')
                self.keyword(parts[0].strip())
                p = ' '.join(parts[1:])
                if p.find(',,') >= 0:
                    self.args = [x.strip() for x in p.split(',,')]
                else :
                    self.args = [p.strip()]

            else :
                self.keyword(s.strip())


    
class OpmlToTree :
    """Mindlessly simplistic and brittle. Uses the minidom"""

    def __init__(self, s) :
        self.dom = parseString(s) # makes the dom tree
        self.root = GWNode('root')
        tag = self.dom.getElementsByTagName('body')[0]
        for child in tag.childNodes :
            if child.nodeType != child.TEXT_NODE :
                self.recurse(self.root, child)
        
    def recurse(self, parent, tag) :
        node = GWNode(tag.getAttribute('text'))
        for child in tag.childNodes :
            if child.nodeType != child.TEXT_NODE :
                self.recurse(node, child)
        parent.addChild(node)
                

