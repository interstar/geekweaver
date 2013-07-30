# Released under the GNU Lesser General Public License, v2.1 or later
# Copyright (c) 2007 Phil Jones <interstar@gmail.com>

import re

# Some miscellaneous helper routines and objects.

def nullFunc(x) : return x

def spaceUnder(s) :
    return re.sub('\s+','_',s)
    
def fromFile(fName, log, cDir) :
    if log != None :
        log.log("Opening file : %s" % cDir + fName)
    f = open(cDir + fName)
    s = f.read()
    f.close()
    return s


class GWException(Exception) :
    def __init__(self, msg, key) :
        self.msg = msg
        self.key = key


class FellowTraveller :
    """
    The routines which run around the tree to execute the program are kept in Mode classes which
    are stateless. However, we also want to pass around a bundle of state, containing things like
    depth in the tree, the current directory etc. The FellowTraveller class holds these pieces of
    information
    """
    def __init__(self, depth, cDir, sideFx) :
        self.depth = depth
        self.cDir = cDir
        self.sideFx = sideFx

    def inc(self) :
        """
        When we recurse, we can't just keep the same object with the depth incremented
        because we want to get the benefits of backing out of the recursion the right way
        This routine creates a new FellowTraveller with an incremented depth
        """
        return FellowTraveller(self.depth+1,self.cDir,self.sideFx)

    def newDir(self,newDir) :
        """ Similar to FellowTraveller.inc, we want a new FellowTraveller with a new cDir"""
        return FellowTraveller(self.depth, newDir, self.sideFx)
        
    def __str__(self) :
        return "&lt;&lt;%s, %s, %s&gt;&gt;" % (self.depth,self.cDir,self.sideFx)
    
def nullFellowTraveller() :
    return FellowTraveller(0,'',lambda x, y : x)

                
class LexPageName :
    """
    Here we're extracting information defining the name of a new page, 
    with optional blockCalls and rename
    Main format :
    &pageName [blockCall] [rename]
    eg.
    &myPage
    which will produce a page called myPage.html
    eg. 2
    &myPage :tpl > main.php
    which will produce a page wrapped in a calls the block tpl and saved to a file called main.php
    This class just cuts up the line into the requisite parts
    """
    def outFile(self, s) :
        m = re.search('>\s*(\S+)',s) 
        if m :
            self.outFileName = m.groups(0)[0]
            i = s.find('>')
            return s[:i].strip()
        else :
            return s.strip()
            
    def __init__(self, s, ext = 'html') :
        self.s = s
        self.matches = False
        self.pageName = ''
        self.outFileName = ''
        self.symbol = ''

        if re.match('&',s) :
            s = s[1:]
            self.matches = True
            s = self.outFile(s)

            if s.find(':') > 0 :
                parts = s.split(':')
                self.pageName = parts[0].strip()
                self.symbol = parts[1].strip()
                               
            else :
                self.pageName = s

            if self.outFileName == '' :
                self.outFileName = self.pageName + '.' + ext


class MultiDispatch :

    def __init__(self) :
        self.d = {}

    def add(self, fName, typeList, f) :
        key = (fName,)
        for x in typeList :
            key = key + (x,)
        self.d[key] = f

    def call(self, fName, argList) :
        key = (fName,)
        for x in argList :
            key = key + (x.__class__ ,)
        f = self.d[key]
        return f(*argList)
        
