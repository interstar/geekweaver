import re

from modes import BaseMode
from gwNode import LexLine


class HtmlMode(BaseMode) :

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


class JavascriptMode(BaseMode) :

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


