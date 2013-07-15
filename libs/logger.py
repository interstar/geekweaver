# Released under the GNU Lesser General Public License, v2.1 or later
# Copyright (c) 2007 Phil Jones <interstar@gmail.com>

from os import removedirs, mkdir, rmdir, getcwd, makedirs

class Logger(list) :

    """
    Manages the logs for GeekWeaver
    """

    def __init__(self) :
        self.index = 0

    def writeFile(self,fName,s) :
        f = open(fName,'w')
        f.write(s)
        f.close()
        
        
    def writeSymTable(self,st) :
        try :
            mkdir('logs')
        except : pass
        fName = 'logs/log%s.html' % self.index
        
        self.index = self.index + 1
        s = st.html().encode('utf-8')
        self.writeFile(fName,s)
        return fName                       
        
    def log(self, s, typ='normal') :
        if typ == 'symTable' :
            fName = self.writeSymTable(s)
            self.append(["<a href='%s'>SymTable</a>"%fName,typ])
        else :
            self.append([s.encode('utf-8'),typ])

    def _str_(self) :
        return '\n'.join([x[0] for x in self])

    def htmlFile(self, fName) :
        
        def proc(x) :
            try :
                if x[1] == 'normal' :
                    r = x[0].replace('<','&lt;')
                elif x[1] == 'error' :
                    r = """<div style='color:red;'>%s</div>""" % x[0].replace('<','&lt;')
                elif x[1] == 'html' :
                    r = """%s""" % x[0]
                else :
                    r = x[0]
                return r
            except :
                print 'Error in Logger.htmlFile %s ' % x
                assert(False)
        
        s = '<html><body><ul>'
        s=s+''.join(['<li>%s</li>' % proc(x) for x in self])
        s = s + '</ul></body></html>'
        self.writeFile(fName,s)
        
