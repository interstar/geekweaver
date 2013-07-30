import re

from gwHelpers import spaceUnder, LexPageName
from modes import BaseMode
from os import removedirs, mkdir, rmdir, getcwd, makedirs
from shutil import copyfile, copytree, copy2


class PrimalMode(BaseMode) :

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


        
class StaticSiteMode(BaseMode) :

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
                
            elif re.match(":copy",x.text) :
                source = (x.text[6:]).strip()
                #only absolute copy
                self.log("Want to copy from %s to %s "%(source,nd))
                copy2(source,nd)
                
            elif re.match(":copytree",x.text) :
                source = (x.text[10:]).strip()
                #only absolute copy
                self.log("Want to copy directory from %s to %s "%(source,nd))
                copytree(source,fellow.cDir + '/')


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

