# Released under the GNU General Public License, v3.0 or later
# Copyright (c) 2007 Phil Jones <interstar@gmail.com>

"""

This is the main interpreter for GeekWeaver
"""

from SymbolTable import *
from gwModes import *

class InterpreterFactory :
    """
    The GeekWeaver interpreter and environment has to wire together several things :
    - an interpreter
    - a general "environment"
    - a Logger, where we can send diagnostic and error messages
    - a SymbolTable (where we can store and retrieve the look-up values of symbols which the program is running)
    - a SitMapper, slightly ill defined, but hopefully to manage building up a map of the site as it's being built

    The InterpreterFactory is used to assemble instances of all these together, so we can avoid too much
    unnecessary dependency.

    Note that we're hardwiring the actual classes into this object at the moment. In future we may make it more
    flexible, but at least, at the moment, it's one place to put all these decisions.
    """


    def __init__(self) :
        self.logger = Logger()
        self.symbolTable = SymbolTable()
        self.siteMapper = SiteMapper(self.logger)
        self.interpreter = Interpreter(self.symbolTable,self.siteMapper)
        self.environment = Environment(self.interpreter,self.symbolTable,self.siteMapper)
        self.interpreter.environment = self.environment
        self.environment.interpreter = self.interpreter

    def getLogger(self) : return self.logger
    def getSymbolTable(self) : return self.symbolTable
    def getSiteMapper(self) : return self.siteMapper
    def getEnvironment(self) : return self.environment
    def getInterpreter(self) : return self.interpreter
    
        

def makeLink(siteRoot, linkText, linkDest, isDir) :
    if isDir :
        imgSrc = '%sfolder.gif' % (siteRoot + '/dTree/img/')
    else : 
        imgSrc = '%spage.gif' % (siteRoot + '/dTree/img/')
        
    return "<li><a href='%s'><img border='0' src='%s'/>&nbsp;%s</a></li>" % (linkDest,imgSrc,linkText)

class PageMaker :
    def __init__(self, tpl) :
        self.tpl = tpl
    def readTpl(self, tplName) :
        self.tpl = Template(fromFile(tplName))
    def write(self, fName, d) :
        f=open(fName,'w')
        s = self.tpl.safe_substitute(d)
        f.write(s)
        f.close()

class Environment :
    def __init__(self, interpreter, symbolTable, siteMapper) :
        self.logger = siteMapper.getLogger()
        self.symbolTable = symbolTable

        self.interpreter = interpreter
        interpreter.environment = self
        
        self.siteMapper = siteMapper
        siteMapper.log = self.logger

        self.currentPageName = ''

        self.compilerDir = (sys.path[0] + '/').replace('\\','/')
        #ab = nullArgBlock()
        #ab['stdlib'] = self.compilerDir + '/standard-library'
        ab = {'stdlib': self.compilerDir + '/standard-library'}
        self.symbolTable.pushFrame(ab)
        
    def siteRoot(self) :
        return self.interpreter.siteRoot()

    def log(self, s, typ='normal') :
        self.logger.log(s,typ)

    def getSymbolTable(self) :
        return self.symbolTable

    def getCurrentPageName(self) :
        return self.currentPageName

class SiteMapper :
    def __init__(self,log) :
        self.log = log
        self.list = []
        self.quickList = []

    def add(self, path, fName, shownName, body) :
        self.list.append(['page',path,fName,shownName,body])
        self.quickList.append(['page',path,fName,shownName])


    def addExternalLink(self,path, fName, shownName) :
        self.list.append(['link',path,fName,shownName])
        self.quickList.append(['link',path,fName,shownName])
        

    def writePage(self, x, subs=[]) :
        try : makedirs(x[1])
        except : pass
        
        name = '%s/%s'%(x[1],x[2])
        self.log.log('process page : creating file : %s ' % name)
        if subs != [] :
            t = Template(x[4])
            s = t.safe_substitute(subs)
        else :
            s = x[4]
        f = open(name, 'w')
        f.write(s)
        f.close()

    def writeAll(self, subs=[]) :
        for x in self.list :
            if x[0] == 'page' :
                self.writePage(x,subs)

    def getLogger(self) :
        return self.log

    def getDir(self,d) :
        return [x[1:] for x in self.quickList if x[1] == d]

    def getULIndex(self,d) :
        return """
<ul>
%s
</ul>""" % ('\n'.join([makeLink(x[0],x[2],x[1],True) for x in self.getDir(d)]))
   
class Interpreter :
    
    def __init__(self, symbolTable, siteMapper) :
        self.tree = None
        
        self.environment = Environment(self,symbolTable,siteMapper)

        self.modes = {}
        self.modes['ur'] = UrMode(self.environment)
        self.modes['primal'] = PrimalMode(self.environment)
        self.modes['staticSite'] = StaticSiteMode(self.environment)
        self.modes['html'] = HtmlMode(self.environment)
        self.modes['htmlForm'] = HtmlFormMode(self.environment)
        self.modes['inter'] = PhpMode(self.environment)
        self.modes['javascript'] = JavascriptMode(self.environment)
        self.modes['data'] = DataMode(self.environment)
        
        self.indexTemplate = None
        self.defaultFileExtension = 'html'
        self.root = ''
        self.codedSiteRoot = '' # if script sets this, it over-rides the calculated one
        self.csvReader = None

    def dumb(self, node, depth=0) :
        print "%s%s" % (('  ' * depth), node.text)
        [self.dumb(x, depth+1) for x in node.children]

    def log(self,s,typ='normal') :
        self.environment.log(s,typ)


    def setSymbolTable(self, symTable) :
        self.environment.symbolTable = symTable

    def getSymbolTable(self) :
        return self.environment.symbolTable

    def getLog(self) :
        return self.environment.logger

    def evalNode(self, tree, modeSelector='html') :
        """Note, if you ask interpreter to eval a node it defaults to 'html' mode"""
        m = self.modes[modeSelector]
        return m.evalNode(tree, nullFellowTraveller())

    def evalSymbols(self, s) :
        return self.mode.evalSymbols(s)

    def setSiteRoot(self, sr) :
        self.codedSiteRoot = sr

    def cwdAsUrl(self) :
        s = getcwd()
        s = 'file:///' + s.replace('\\','/')
        return s

    def siteRoot(self) :
        if self.codedSiteRoot != '' :
            return self.codedSiteRoot
        return '%s/%s' % (self.cwdAsUrl(),self.dName)

    def getRelativeRoot(self, depth) :
        return '../' * depth


    def opmlFileToTree(self, fName) :
        self.log('reading, parsing and building tree %s'%fName)
        xml = fromFile(fName, self.getLog(), '')
        ot = OpmlToTree(xml)
        return ot.root

    
    def runFile(self, fName, dName, packages) :    
        self.log('runFile %s, %s' % (fName,dName))
        self.fName = fName # source file
        self.path = getcwd()
        self.dName = dName # destination directory

        sp = self.environment.compilerDir
        
        self.log('read and parse source file')
        self.tree = self.opmlFileToTree(fName)

        self.log('make directory %s' % dName)
        self.log("<a href='%s'>%s</a>" % (dName,dName),'link')
        mkdir(self.dName)

        self.log('copy standard-library blocks')
        copytree(sp + 'standard-library/blocks',self.dName + '/blocks')

        self.log('copy templates')
        mkdir(self.dName + '/templates/')
        copytree(sp + 'standard-library/site-templates/default',self.dName + '/templates/default')

        for p in packages :
            self.log('copy template packages : %s' % p)
            copytree(sp + 'standard-library/site-templates/%s'%p, self.dName + '/templates/%s'%p)
      
        self.log('copy dtree')
        copytree(sp + 'standard-library/dtree',self.dName + '/dtree')

        self.log('loading standard template')
        self.indexTemplate = Template(fromFile(sp + 'standard-library/site-templates/default/template.html', self.getLog(),''))

        self.log('loading default page tree')
        defaultTree = self.opmlFileToTree(sp + 'standard-library/blocks/default-page.opml')

        self.modes['ur'].evalNode(defaultTree,FellowTraveller(0,self.dName,lambda x, y : x) )

        self.log('eval root')
        try :
            self.log('Evaluating Tree')
            self.modes['primal'].evalNode(self.tree, FellowTraveller(0,self.dName,lambda x, y : x))
            self.log('Creating Files')
            self.environment.siteMapper.writeAll()
            self.log('Writing Control Panel')
            self.controlPanel(self.dName)
            self.log('GeekWeaving Completed')
        except Exception, e :
            print """There was an error. Check log.html
%s """ % e
            self.log('%s' % e,'error')
            self.getLog().htmlFile('log.html')


    def controlPanel(self, cDir='.') :
        self.log('writing frameset')
        f = open('%s/index.html' % cDir,'w')
        f.write("""
<frameset cols="25%,75%">
   <frame src="menu.html">
   <frame name="controlmain">
</frameset>""")
        f.close()
        self.log('writing menu')
        f = open('%s/menu.html' % cDir,'w')
        f.write(self.makeMenuPage())
        f.close()
        

    def makeMenuPage(self) :
        return """
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
        <link rel="StyleSheet" href="./dtree/dtree.css" type="text/css">
        <script type="text/javascript" src="./dtree/dtree.js"></script>
    </head>
    <body>
    <h3>GeekWeaver</h3>
    <p>
    <A href="../log.html" target="controlmain">Log</a>
    </p>
    %s
    </body>
</html>        
""" % self.siteMap


        
    def indexPage(self, text, index, fellow) :
        def ml(root,x0,x1,x2) :
            if not re.match('//',x0) :
                return makeLink(root,x0,x1,x2)
            else : return ''
    
        self.log('in indexPage %s . index is %s' % (text,index))
        childLinks = '\n'.join([ml(self.siteRoot(),x[0],x[1],x[2]) for x in index ])

        if text[0] == '&' : text = text[1:]
        
        p = PageMaker(self.indexTemplate)
        p.write('%s/index.html' % fellow.cDir,
                { 'title' : text,
                  'root' : self.siteRoot(),
                  'leftGutter' : """<a href="../index.html">Up</a>""" ,
                  'mainTop' : text,
                  'tagline' : '',
                  'main' : """
<div>
<ul>
%s
</ul>
</div>
""" % childLinks
                }
        )


    def makeSiteMap(self, tree, fellow) :
        self.log('Interpreter.makeSiteMap')
        self.log('tree.text = %s' % tree.text)
        
        self.siteMapId = 1
        
        self.siteMap = """
<div class="dtree">

	<p><a href="javascript: d.openAll();">open all</a> | <a href="javascript: d.closeAll();">close all</a></p>

	<script type="text/javascript">
		<!--

		d = new dTree('d','%s');

		d.add(0,-1,'Home','%s','','controlmain');
                %s
		document.write(d);
		d.openAll();

		//-->
	</script>

</div>        
""" % (self.siteRoot()+'/',self.siteRoot() + '/%s/index.html' % spaceUnder(tree.text[1:]),
       '\n		'.join(
        [ self.rSiteMap(x,0,
                FellowTraveller(0,self.siteRoot() + ('/%s/'%spaceUnder(tree.text[1:])),lambda a,b : a)) for x in tree.children ]
          )
       )
        self.log('makeSiteMap : made siteMap : %s' % self.siteMap)
        return self.siteMap
        
    def rSiteMap(self, node, parentId, fellow) :
        self.log('rSiteMap : %s' % node.text)
        sm = ''
        self.siteMapId = self.siteMapId + 1
        s = node.text
        lpn = LexPageName(s)
        if s == '' :
            return ''
        elif s[0] == ':' :
            pass
        elif s[0] == '@' :
            pass
        elif re.match('//',s) :
            pass
        elif re.match('>\s*(.+)\s*>\s*(\S+)',s) :
            m = re.match('>\s*(.+)\s*>\s*(\S+)',s)
            linkText = m.groups(0)[0]
            dest = m.groups(0)[1]
            sm = sm + """
            d.add(%s,%s,"%s","%s","%s",'controlmain');
""" % (self.siteMapId, parentId, linkText, dest, lpn.pageName)
            
        elif lpn.matches :
            sm = sm + """
            d.add(%s,%s,"%s","%s/%s","%s",'controlmain');
		""" % (self.siteMapId, parentId, lpn.pageName, fellow.cDir, spaceUnder(lpn.outFileName),lpn.pageName)
        else :
            # it's a subdirectory
            sm = sm + """
            d.add(%s,%s,"%s","%s/%s/index.html",'index','controlmain');
		""" % (self.siteMapId, parentId, node.text, fellow.cDir, spaceUnder(node.text))

            thisId = self.siteMapId
            for c in node.children :
                sm = sm + self.rSiteMap(c, thisId, fellow.newDir('%s/%s/' % (fellow.cDir, spaceUnder(s)))) 

        return sm

