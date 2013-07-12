# Released under the GNU General Public License, v3.0 or later
# Copyright (c) 2007 Phil Jones <interstar@gmail.com>

"""
SymbolTable is a dictionary of stacks (lists)
"""

class SymbolTableException(Exception):
    def __init__(self, msg, frame, key) :
        self.msg = msg
        self.frame = frame
        self.key = key
                 
class SymbolFrame :
    """ One frame (dictionary) binding names to values"""
    def __init__(self,d={},parent=None,depth=0) :
        self.d = d
        self.parent = parent
        self.depth = depth

    def get(self,k) :
        if self.d.has_key(k) :
            return self.d[k]
        else :
            if self.parent :
                return self.parent.get(k)
            else :
                
                raise SymbolTableException("Key Not Defined",self,k)

    def __str__(self) :
        return "SymbolFrame depth %s" % self.depth

    def html(self) :
        s = """<tr>
<td valign='top'>%s</td><td valign='top'>%s</td>
<td valign='top'>
<table border='1'>""" % (self.depth, self.parent)
        for k in self.d.keys() :
            v = '%s' % self.d[k]
            v = v.replace('<','&lt;')
            s = s + '<tr><td>%s</td><td>%s</td></tr>\n' % (k,v)
        s = s + """</table>
</td></tr>
"""
        return s
    
class SymbolTable :
    """ New version of the symbol table in terms of a 'stack' or 'tree' of SymbolFrames """
    
    def __init__(self, d = {}) :
        # symbol table always starts with one frame, empty if dict not specified
        self.stack = [SymbolFrame(d,None,0)]
        
    def get(self, k) :
        return self.stack[-1].get(k)
    
    def pushFrame(self, d) :
        # We're going to assume that the d which is pushed into the SymbolTable is
        # actually an ArgBlock rather than a dictionary (although it is a sub-class of dict)
        
        if len(self.stack) > 1 :
            parent = self.stack[-1]
            sf = SymbolFrame(d,parent, parent.depth+1)
        else :
            sf = SymbolFrame(d,None,0)
        self.stack.append(sf)
        
    def popFrame(self) :
        self.stack.pop()

    def getCurrentLineArgs(self) :
        return self.stack[-1].d.lineArgs

    def getCurrentAnonChildren(self) :
        return self.stack[-1].d.getAnonChildren()



    def depth(self) :
        return len(self)

    def __len__(self) :
        return len(self.stack)

    def __str__(self) :
        return "Symbol Table"
   
    def html(self) :
        return """<h3>Symbol Table</h3>
<table border='2'>
<tr><td>Frame</td><td>Parent</td><td>Frame Contents</td></tr>

%s
</table>
""" % ('\n'.join([sf.html() for sf in self.stack ]))
