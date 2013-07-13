
import unittest
import string

import libs.gwNode
from libs.SymbolTable import *
import libs.gwModes 
from libs.interpreter import * 

class TestMiscTools(unittest.TestCase) :

    def testSU(self) :
        self.assertEquals(spaceUnder('ab cd ef/xy z'),'ab_cd_ef/xy_z')

    def testMultiDispatch(self) :
        md = MultiDispatch()
        
        md.add("f", [str,str], lambda x,y : x + y)
        md.add("f", [str,int], lambda x,y : "%s : (%s)" % (x,y))
        self.assertEquals(md.call("f",("aa","bb")),"aabb")
        self.assertEquals(md.call("f",("aa",4)),"aa : (4)")

    
class TestSymbolTable(unittest.TestCase) :
    
    def testSymbolTable(self) :
        st = SymbolTable()
        self.assertEquals(st.depth(),1)

        st.pushFrame({"hello" : "teenage america",
                 "goodbye" : "cruel world"})
        self.assertEquals(st.get("hello"),"teenage america")
        self.assertEquals(st.get("goodbye"),"cruel world")

        self.assertEquals(st.depth(),2)
        st.pushFrame({"hello" : "coal black smith"})
        self.assertEquals(st.get("hello"),"coal black smith")
        self.assertEquals(st.get("goodbye"),"cruel world")
        self.assertEquals(st.get("hello"),"coal black smith")
        self.assertEquals(st.depth(),3)
        st.popFrame()
        self.assertEquals(st.get("hello"),"teenage america")
        self.assertEquals(st.get("goodbye"),"cruel world")
        self.assertEquals(st.depth(),2)

        for x in range(10) :
            st.pushFrame({'x':'%s'%x, 'y':'%s'%x*x})
        for y in range(9,0,-1) :
            self.assertEquals(st.get("hello"),"teenage america")
            self.assertEquals(st.get('x'),'%s'%y)
            st.popFrame()


class testLexers(unittest.TestCase) :

    def testLexLine(self) :
        ll = LexLine('.class','.')
        self.assertEquals(ll.matches,True)
        self.assertEquals(ll.cls,'class')
        self.assertEquals(ll.id,'')
        self.assertEquals(ll.args,[])
        ll = LexLine('.class','*')
        self.assertEquals(ll.matches,False)
        self.assertEquals(ll.cls,'')
        self.assertEquals(ll.id,'')
        ll = LexLine('.happy;fred','.')
        self.assertEquals(ll.matches,True)
        self.assertEquals(ll.cls,'happy')
        self.assertEquals(ll.id,'fred')
        
        ll = LexLine('.happy;fred 1,, 2,, 3','.')
        self.assertEquals(ll.matches,True)
        self.assertEquals(ll.cls,'happy')
        self.assertEquals(ll.id,'fred')
        self.assertEquals(ll.args,['1','2','3'])

        ll = LexLine('#@ csvName','#@')
        self.assertEquals(ll.matches,True)
        self.assertEquals(ll.key,'csvName')

        ll = LexLine('#@ csvName ;','#@')
        self.assertEquals(ll.matches,True)
        self.assertEquals(ll.args[0],';')

        self.assertEquals(ll.key,'csvName')


    def testLexPageName(self) :
        lpn = LexPageName('not a page')
        self.assertEquals(lpn.matches,False)
        
        lpn = LexPageName('&main')
        self.assertEquals(lpn.matches,True)
        self.assertEquals(lpn.pageName,'main')
        self.assertEquals(lpn.symbol,'')
        
        lpn = LexPageName('&main :page')
        self.assertEquals(lpn.matches,True)
        self.assertEquals(lpn.pageName,'main')
        self.assertEquals(lpn.outFileName,'main.html')
        self.assertEquals(lpn.symbol,'page')
        
        lpn = LexPageName('&main > zmain')
        self.assertEquals(lpn.matches,True)
        self.assertEquals(lpn.pageName,'main')
        self.assertEquals(lpn.outFileName,'zmain')
        
        lpn = LexPageName('&main    > main.xml')
        self.assertEquals(lpn.matches,True)
        self.assertEquals(lpn.pageName,'main')
        self.assertEquals(lpn.outFileName,'main.xml')

        lpn = LexPageName('&main  :svgDiag  > main.svg')
        self.assertEquals(lpn.matches,True)
        self.assertEquals(lpn.pageName,'main')
        self.assertEquals(lpn.outFileName,'main.svg')
        self.assertEquals(lpn.symbol,'svgDiag')


class TestGWNode(unittest.TestCase) :

    def testGWNode(self) :
        t = GWNode('hello')
        self.assertEquals(t.__class__,GWNode)
        t = GWNode('hello').addChild('world')
        self.assertEquals(t.children[0].__class__, GWNode)
        self.assertEquals(t.children[0].text, 'world')
        self.assertEquals(t.size(t),2)
        t = GWNode('hello').addChild(GWNode('teenage').addChild('america'))
        self.assertEquals(t.size(t),3)
        t.addChild('coal black smith')
        self.assertEquals(t.size(t),4)
        self.assertEquals(t.children[0].children[0].text,'america')

        self.assertEquals(t.matches('hell'),True)
        self.assertEquals(t.matches('heaven'),False)
        self.assertEquals(GWNode('&&data').matches('&&data'),True)
        self.assertEquals(GWNode('&&xyz').matches('&&data'),False)

        ts = "abc"
        tn = GWNode(ts)
        tl = [tn]
        
        self.assertTrue(isNode(tn))
        self.assertFalse(isNode(tl))
        self.assertFalse(isNode(ts))

        self.assertFalse(isList(ts))
        self.assertTrue(isList(tl))
        self.assertFalse(isList(tn))

        self.assertFalse(isStr(tl))
        self.assertFalse(isStr(tn))
        self.assertTrue(isStr(ts))

                          

class TestArgBlock(unittest.TestCase) :

    def buildInterpreter(self) :
        i = Interpreter(SymbolTable(),SiteMapper(Logger()))
        return i

    def testArgBlock(self) :
        t = GWNode('__ a,, b,, c')
        t.addChild(GWNode('x : 1'))
        t.addChild(GWNode('y : 2'))
        t.addChild(GWNode('these'))
        t.addChild(GWNode('are'))
        t.addChild(GWNode('child'))
        t.addChild(GWNode('args'))

        t2=GWNode('z : ')
        t2.addChild(GWNode('has'))
        t2.addChild(GWNode(' more'))
        t.addChild(t2)

        t2=GWNode('something')
        t2.addChild(GWNode(' further'))
        t2.addChild(GWNode(' with more'))
        t.addChild(t2)

        i = self.buildInterpreter()
        m = i.modes['ur']
        ab = m.makeArgBlock(t)
        self.assertEquals(ab.__class__,ArgBlock)
        self.assertEquals(len(ab.keys()),13)
        self.assertEquals(ab['_0'],'a')
        self.assertEquals(ab['_1'],'b')
        self.assertEquals(ab['_2'],'c')

        self.assertEquals(ab['x'],'1')
        self.assertEquals(ab['y'],'2')

        self.assertEquals(ab['__0'],'these')
        self.assertEquals(ab['__1'],'are')
        self.assertEquals(ab['__2'],'child')
        self.assertEquals(ab['__3'],'args')

        self.assertEquals(ab['z'],'has more')

        self.assertEquals(ab['__4'],'something further with more')
        
        t.text = ':blockCall a,, b,, c'
        ab = m.makeArgBlock(t)
        self.assertEquals(len(ab.keys()),13)
        self.assertEquals(ab['_0'],'a')
        self.assertEquals(ab['x'],'1')
        self.assertEquals(ab['__4'],'something further with more')

        self.assertEquals(ab['_'].__class__,GWNode)
        self.assertEquals(ab['__'].__class__,GWNode)
        self.assertEquals(ab['_'].children[0].text,'a')
        self.assertEquals(ab['__'].children[0].text,'these')
        
        

    def testDataArgs(self) :
        t2 = GWNode('example data')
        t3 = GWNode('more')
        t = GWNode(':f')
        data = GWNode('data #').addChild(t2)
        
        t.addChild(data)
        data.addChild(t3)
        
        i = self.buildInterpreter()
        m = i.modes['ur']
        ab = m.makeArgBlock(t)

        self.assertEquals(ab['data'].children[0],t2)
        self.assertEquals(ab['data'].children[1],t3)


 
class TestEvalSymbol(unittest.TestCase) :

    def buildInterpreter(self) :
        i = Interpreter(SymbolTable(),SiteMapper(Logger()))
        return i

    def testEvalSymbol(self) :
        i = self.buildInterpreter()
        i.getSymbolTable().pushFrame({"x" : "world"})
        m = i.modes["ur"]
        self.assertEquals(m.evalSymbols("hello $x",nullFellowTraveller()),"hello world")
        self.assertEquals(m.evalSymbols("hello $/x/magazine/",nullFellowTraveller()),"hello world")
        self.assertEquals(m.evalSymbols("hello $/y/magazine/",nullFellowTraveller()),"hello magazine")
        
        self.assertEquals(m.evalSymbols("hello $x $x",nullFellowTraveller()),"hello world world")      
        self.assertEquals(m.evalSymbols("hello $/x/magazine/ $/x/magazine/",nullFellowTraveller()),"hello world world")
        self.assertEquals(m.evalSymbols("hello $/y/magazine/ $/y/magazine/",nullFellowTraveller()),"hello magazine magazine")
        
        self.assertEquals(m.evalSymbols("hello $/y/$x/",nullFellowTraveller()),"hello world")

        m = i.modes["staticSite"]
        self.assertEquals(m.evalSymbols("&$/y/$x/ wide web",nullFellowTraveller()),"&world wide web")

        self.assertEquals(m.evalSymbols(":$/x// a,, b,, c",nullFellowTraveller()),":world a,, b,, c")

    def testEvalWithData(self):
        i = self.buildInterpreter()
        t = GWNode('hello')
        t.addChild(GWNode(' teenage'))
        t.addChild(GWNode(' america'))           
        i.getSymbolTable().pushFrame({"zewp" : t})
        m = i.modes["ur"]
        self.assertEquals(m.evalSymbols("$zewp",nullFellowTraveller()),"hello teenage america")
        self.assertEquals(m.evalSymbols("$zewp[0]",nullFellowTraveller())," teenage")
        self.assertEquals(m.evalSymbols("$zewp[1]",nullFellowTraveller())," america")
        self.assertEquals(m.evalSymbols("$zewp[.]",nullFellowTraveller()),"hello")

        self.assertEquals(m.evalSymbols('#zewp',nullFellowTraveller()),t)

        
    
class TestModes(unittest.TestCase) :

    def buildInterpreter(self) :
        i = Interpreter(SymbolTable(),SiteMapper(Logger()))
        return i


    def testBasicEval(self) :
        i = self.buildInterpreter()

        t = GWNode('.myClass')
        self.assertEquals(i.evalNode(t),"<div class='myClass'></div>")

        t = GWNode('.myClass Some Stuff')
        self.assertEquals(i.evalNode(t),"<div class='myClass'>Some Stuff</div>")
        
        t = GWNode(';myId')
        self.assertEquals(i.evalNode(t),"<div id='myId'></div>")

        t = GWNode(';myId Some Stuff')
        self.assertEquals(i.evalNode(t),"<div id='myId'>Some Stuff</div>")

        t = GWNode('> NooRanch > http://www.nooranch.com')
        self.assertEquals(i.evalNode(t),"<a href='http://www.nooranch.com'>NooRanch</a>")

        i.setSiteRoot('http://www.geekweaver.com/')
        t = GWNode(' hello [[teenage/america.html world]] and more')
        self.assertEquals(i.evalNode(t)," hello <a href='http://www.geekweaver.com/teenage/america.html'>world</a> and more")
        
        t = GWNode(']myImg.gif')
        self.assertEquals(i.evalNode(t),"<img src='myImg.gif' alt=''/>")

        t = GWNode(']myImg.gif Alt Text')
        self.assertEquals(i.evalNode(t),"<img src='myImg.gif' alt='Alt Text'/>")

        t = GWNode('.<mytag>')
        t2 = GWNode('hello xml')
        t.addChild(t2)
        self.assertEquals(i.evalNode(t),"""<mytag>hello xml</mytag>""")

        t = GWNode('.<mytag atr="1">')
        t2 = GWNode('hello xml')
        t.addChild(t2)
        self.assertEquals(i.evalNode(t),"""<mytag atr="1">hello xml</mytag>""")

        t = GWNode('.<mytag a="1" b="2">')
        t2 = GWNode('hello xml')
        t.addChild(t2)
        self.assertEquals(i.evalNode(t),"""<mytag a="1" b="2">hello xml</mytag>""")


        t = GWNode('<mytag>')
        t2 = GWNode('hello xml')
        t.addChild(t2)
        self.assertEquals(i.evalNode(t),"""<mytag>hello xml""")
    
        t = GWNode('')
        self.assertEquals(i.evalNode(t),'')

        t = GWNode('// jfhj').addChild(GWNode('blah blah blah'))
        self.assertEquals(i.evalNode(t),'')        

    

    def testBlockEvals(self) :
        i = self.buildInterpreter()
        self.assertEquals(i.tree,None)
        self.assertEquals(i.getSymbolTable().__class__, SymbolTable)

        i.getSymbolTable().pushFrame({'x' : 'teenage', 'y' : 'america'})
        mode = i.modes['html']
        self.assertEquals(mode.evalSymbols('hello $x $y',nullFellowTraveller()),'hello teenage america')

        self.assertEquals(mode.evalSymbols('goodbye $z',nullFellowTraveller()),'goodbye $z')

        # simple block
        t = GWNode('::block').addChild(GWNode('goodbye $name'))

        i.getSymbolTable().pushFrame({'block' : CBlock('block',t,mode)})

        t3 = GWNode('hello teenage america')
        self.assertEquals(mode.evalNode(t3,nullFellowTraveller()),'hello teenage america')
        
        t4 = GWNode(':block')

        self.assertEquals(mode.evalNode(t4,nullFellowTraveller()),'goodbye $name')
                                     
        t5 = GWNode('name : cruel world')
        t4.addChild(t5)

        self.assertEquals(mode.evalNode(t4,nullFellowTraveller()),'goodbye cruel world')

        tx = GWNode(':block').addChild(GWNode('name :').addChild(GWNode('.<p>').addChild(GWNode('porkpie hat'))))

        self.assertEquals(i.evalNode(tx,'html'),'goodbye <p>porkpie hat</p>')

        i2 = self.buildInterpreter()
        t0 = GWNode('root')
        t0.addChild(t)
        t0.addChild(t3)
        t0.addChild(t4)
        mode = i2.modes['html']
                        
        self.assertEquals(mode.evalNode(t0,nullFellowTraveller()),'roothello teenage americagoodbye cruel world')

        t6 = GWNode(':block')
        t7 = GWNode('name:')
        t8 = GWNode('.c')
        t9 = GWNode('w00t!')
        t6.addChild(t7)
        t7.addChild(t8)
        t8.addChild(t9)

        t0.addChild(t6)
        self.assertEquals(mode.evalNode(t0,nullFellowTraveller()),"roothello teenage americagoodbye cruel worldgoodbye <div class='c'>w00t!</div>")
        

        t0 = GWNode('')
        t1 = GWNode('! "%s" % (5 * 5 * 5)')
        t0.addChild(t1)
        self.assertEquals(i2.evalNode(t0),'125')
        
        
        t = GWNode('*myList')
        self.assertEquals(i2.evalNode(t),"<ul class='myList'></ul>")

        t1 = GWNode("cat")
        t2 = GWNode("dog")
        t.addChild(t1)
        t.addChild(t2)
        self.assertEquals(i2.evalNode(t),"""<ul class='myList'>
<li>cat</li>
<li>dog</li></ul>""")

        t2.addChild(GWNode('wolf'))
        


    def testForm(self) :
        i2 = self.buildInterpreter()
        t = GWNode("?myForm -> http://www.server.com/get")
        self.assertEquals(i2.evalNode(t),"<form name='myForm' method='GET' action='http://www.server.com/get'>\n</form>")
        t.addChild(GWNode("??hello"))
        self.assertEquals(i2.evalNode(t),"""<form name='myForm' method='GET' action='http://www.server.com/get'>
<input name='hello'/>
</form>""")
        t.addChild(GWNode("??Age:teenage"))
        self.assertEquals(i2.evalNode(t),"""<form name='myForm' method='GET' action='http://www.server.com/get'>
<input name='hello'/>
Age : <input name='teenage'/>
</form>""")
        t1 = GWNode('?*fruit')
        t1.addChild(GWNode('1:orange'))
        t1.addChild(GWNode('2:apple'))
        t1.addChild(GWNode('3:banana'))
        t.addChild(t1)
        self.assertEquals(i2.evalNode(t),"""<form name='myForm' method='GET' action='http://www.server.com/get'>
<input name='hello'/>
Age : <input name='teenage'/>
<select name='fruit'>
<option value='1'>orange</option>
<option value='2'>apple</option>
<option value='3'>banana</option>
</select>
</form>""")

        t.addChild(GWNode('[]'))
        self.assertEquals(i2.evalNode(t),"""<form name='myForm' method='GET' action='http://www.server.com/get'>
<input name='hello'/>
Age : <input name='teenage'/>
<select name='fruit'>
<option value='1'>orange</option>
<option value='2'>apple</option>
<option value='3'>banana</option>
</select>
<input type='submit'/>
</form>""")

        t.addChild(GWNode('[Go]'))
        self.assertEquals(i2.evalNode(t),"""<form name='myForm' method='GET' action='http://www.server.com/get'>
<input name='hello'/>
Age : <input name='teenage'/>
<select name='fruit'>
<option value='1'>orange</option>
<option value='2'>apple</option>
<option value='3'>banana</option>
</select>
<input type='submit'/>
<input value='Go' type='submit'/>
</form>""")

        t.addChild(GWNode('[Go ;goButton]'))
        self.assertEquals(i2.evalNode(t),"""<form name='myForm' method='GET' action='http://www.server.com/get'>
<input name='hello'/>
Age : <input name='teenage'/>
<select name='fruit'>
<option value='1'>orange</option>
<option value='2'>apple</option>
<option value='3'>banana</option>
</select>
<input type='submit'/>
<input value='Go' type='submit'/>
<input value='Go' name='goButton' type='button'/>
</form>""")

        t.text = "?myForm => http://www.server.com/post"
        ta = GWNode('?_ Description: desc ')
        t.addChild(ta)
        self.assertEquals(i2.evalNode(t),"""<form name='myForm' method='POST' action='http://www.server.com/post'>
<input name='hello'/>
Age : <input name='teenage'/>
<select name='fruit'>
<option value='1'>orange</option>
<option value='2'>apple</option>
<option value='3'>banana</option>
</select>
<input type='submit'/>
<input value='Go' type='submit'/>
<input value='Go' name='goButton' type='button'/>
Description : <textarea name='desc'>
</textarea>
</form>""")

        ta.text = '?_ desc '
        self.assertEquals(i2.evalNode(t),"""<form name='myForm' method='POST' action='http://www.server.com/post'>
<input name='hello'/>
Age : <input name='teenage'/>
<select name='fruit'>
<option value='1'>orange</option>
<option value='2'>apple</option>
<option value='3'>banana</option>
</select>
<input type='submit'/>
<input value='Go' type='submit'/>
<input value='Go' name='goButton' type='button'/>
<textarea name='desc'>
</textarea>
</form>""")


    def testListAndTableAsFunctionArgs(self) :
        i = self.buildInterpreter()
        t = GWNode('')
        t2 = GWNode('::f')
        t21 = GWNode('.class').addChild('$__0')
        t2.addChild(t21)
        t.addChild(t2)
        t3 = GWNode(':f')
        t.addChild(t3)
        t4 = GWNode('*cls')
        t4.addChild(GWNode('a'))
        t4.addChild(GWNode('b'))
        t4.addChild(GWNode('c'))
        t3.addChild(t4)
        self.assertEquals(i.evalNode(t),"""<div class='class'><ul class='cls'>
<li>a</li>
<li>b</li>
<li>c</li></ul></div>""")
        
    def testArgsList(self) :
        i = self.buildInterpreter()
        t = GWNode('')
        t2 = GWNode('::argtest')
        t2.addChild( GWNode('xxx $_0 $_1 $_2'))
        t4 = GWNode(':argtest hello,, teenage,, america')
        t.addChild(t2)
        t.addChild(t4)
        i.evalNode(t)
        
        self.assertEquals(i.evalNode(t),"""xxx hello teenage america""")

    def testRep(self) :
        i = self.buildInterpreter()
        t = GWNode('xxx')
        t2 = GWNode('::rep')
        t2.addChild(GWNode('hello $name'))
        t3 = GWNode(':* rep')
        t4 = GWNode('')
        t4.addChild(GWNode('name : fred'))
        t5 = GWNode('')
        t5.addChild(GWNode('name : maria'))
        t6 = GWNode('')
        t6.addChild(GWNode('name : andrea'))
        t3.addChild(t4)
        t3.addChild(t5)
        t3.addChild(t6)
        t.addChild(t2)
        t.addChild(t3)
        self.assertEquals(i.evalNode(t),"""xxxhello fredhello mariahello andrea""")
        

    def testNamedTransitions(self) :
        st = SymbolTable()
        i = self.buildInterpreter()
        i.setSymbolTable(st)
        t = GWNode('blah')
        t2 = GWNode('&&htmlForm')
        t2.addChild(GWNode('[Form Mode]'))
        t.addChild(t2)
        i.evalNode(t)
        i.getLog().htmlFile('log.html')
        self.assertEquals(i.evalNode(t),"""blah\n<input value='Form Mode' type='submit'/>""")

    def testPHP(self) :
        i = self.buildInterpreter()
        t = GWNode('')
        t2 = GWNode('&&inter')
        t2.addChild(GWNode('=arg'))
        t.addChild(t2)
        i.evalNode(t)
        i.getLog().htmlFile('log.html')
        self.assertEquals(i.evalNode(t),"""<? $arg = $HTTP_GET_VARS['arg']; ?>""")        
        t3 = GWNode('.c')
        t3.addChild(GWNode('hello %arg and %more'))
        t2.addChild(t3)
        i.evalNode(t)
        i.getLog().htmlFile('log.html')
        self.assertEquals(i.evalNode(t),"""<? $arg = $HTTP_GET_VARS['arg']; ?><div class='c'>hello <? echo $arg ?> and <? echo $more ?></div>""")
        t = GWNode('')
        t2 = GWNode('&&inter')
        t.addChild(t2)
        t3 = GWNode('?:') 
        t4 = GWNode("($arg < 0)")
        t4.addChild(GWNode("echo 'less';"))
        t5 = GWNode("($arg == 0)").addChild(GWNode('"""').addChild(GWNode('equals')))
        t6 = GWNode(" else ")
        t7 = GWNode('"""')
        t7.addChild(GWNode('more'))
        t6.addChild(t7)
        t2.addChild(t3)
        t3.addChild(t4)

        i.evalNode(t)
        i.getLog().htmlFile('log.html')
        self.assertEquals(i.evalNode(t),"""<? if ($arg < 0) {
echo 'less';
} ?>""")
        t3.addChild(t5)
        t3.addChild(t6)
        self.assertEquals(i.evalNode(t),"""<? if ($arg < 0) {
echo 'less';
} elseif ($arg == 0) {
echo 'equals';
} else {
echo 'more';
} ?>""")
        t = GWNode('').addChild(GWNode('&&inter').addChild(GWNode('"""').addChild('hello teenage america')))
        self.assertEquals(i.evalNode(t),"""echo 'hello teenage america';""")

    def testJavascript(self) :
        i = self.buildInterpreter()
        t = GWNode('&&javascript').addChild(GWNode('define f(x) {').addChild(GWNode(' return x*x;').addChild('}')))
        self.assertEquals(i.evalNode(t),"""define f(x) {
 return x*x;
}
""")
                                        
    def testDataTypes(self) :
        i = self.buildInterpreter()
        t2 = GWNode('aaa')
        t = GWNode("&&data").addChild(t2)
        x = i.evalNode(t)
        self.assertTrue(isNode(x))
        self.assertEquals(len(x.children),1)
        self.assertEquals(x.children[0],t2)

        t = GWNode('')
        cell = GWNode('::cell').addChild(GWNode('<td class="$__1[0]">$__0[0]</td>'))
        t.addChild(cell)
    
        
        call1 = GWNode(':cell')
        t2 = GWNode('&&data').addChild(GWNode('a'))
        t3 = GWNode('&&data').addChild(GWNode('b'))
        call1.addChild(t2)
        call1.addChild(t3)
        t.addChild(call1)
        self.assertEquals(i.evalNode(t),"""<td class="b">a</td>""")

        t = GWNode('')

        cell = GWNode('::cell').addChild(GWNode('<td>$__0[0]</td>'))
        t.addChild(cell)

        row = GWNode('::row')
        row.addChild(GWNode('<tr>'))
        row.addChild(GWNode(':for cell,, #d'))
        row.addChild(GWNode('</tr>'))
        t.addChild(row)

        call2 = GWNode(':row')
        dArg = GWNode('d #')
        call2.addChild(dArg)
        
        dArg.addChild('hello')
        dArg.addChild('world')
        
        t.addChild(call2)
        
        
        #self.assertEquals(i.evalNode(t),"<tr><td>hello</td></td>world</td></tr>")
        """
        table = GWNode('::table')
        table.addChild(GWNode('<table>'))
        table.addChild(GWNode(':for #_0,, row'))
        table.addChild(GWNode('</table>'))
        t.addChild(cell)
        t.addChild(row)
        t.addChild(table)
        
        data = GWNode('&&data')
        r1 = GWNode('')
        r1.addChild(GWNode('apples'))
        r1.addChild(GWNode('oranges'))
        r1.addChild(GWNode('pears'))
        
        r2 = GWNode('')
        r2.addChild(GWNode('5'))
        r2.addChild(GWNode('4'))
        r2.addChild(GWNode('6'))
        
        data.addChild(r1)
        data.addChild(r2)

        call = GWNode(':table')
        
        t.addChild(call)
        call.addChild(data)"""
        
        #self.assertEquals(i.evalNode(t),"""<table><tr><td>apples</td><td>oranges</td><td>pears</td></tr><tr><td>5</td><td>4</td><td>6</td></tr></table>""")

    def testFors(self) :
        i = self.buildInterpreter()
        t = GWNode('')
        row = GWNode('::rows')
        for1 = GWNode(':for x,, #data')
        tr = GWNode('.<tr>')
        for2 = GWNode(':for y,, #x')
        td = GWNode('.<td>').addChild('$y')
        t.addChild(row)
        row.addChild(for1)
        for1.addChild(tr)
        tr.addChild(for2)
        for2.addChild(td)

        call = GWNode(':rows')
        data = GWNode('data #')
        r1 = GWNode('r1')
        r1.addChild(GWNode('oranges'))
        r1.addChild(GWNode('apples'))

        r2 = GWNode('r2')
        r2.addChild(GWNode('4532'))
        r2.addChild(GWNode('389'))

        data.addChild(r1)
        data.addChild(r2)
        call.addChild(data)
        t.addChild(call)

        self.assertEquals(i.evalNode(t),"""<tr><td>oranges</td><td>apples</td></tr><tr><td>4532</td><td>389</td></tr>""")
        
        lineBlock = GWNode('::lb').addChild(GWNode(':for x,, #_').addChild('<td>$x</td>'))
        call = GWNode(':lb 1,, 2,, 3')
        t = GWNode('')
        t.addChild(lineBlock)
        t.addChild(call)
        
        self.assertEquals(i.evalNode(t),'<td>1</td><td>2</td><td>3</td>')

        call = GWNode(':lb')
        call.addChild(GWNode('a'))
        call.addChild(GWNode('b'))
        call.addChild(GWNode('c'))
        call.addChild(GWNode('d'))

        lineBlock = GWNode('::lb').addChild(GWNode(':for x,, #__').addChild('<td>$x</td>'))
        t = GWNode('')
        t.addChild(lineBlock)
        t.addChild(call)
        
        self.assertEquals(i.evalNode(t),'<td>a</td><td>b</td><td>c</td><td>d</td>')

        

class TestInterpreter(unittest.TestCase) :

    def buildInterpreter(self) :
        i = Interpreter(SymbolTable(),SiteMapper(Logger()))
        return i

    def testRelativeRoot(self) :
        i = self.buildInterpreter()
        self.assertEquals(i.getRelativeRoot(4),'../../../../')

    def testForRefactoring(self) :
        st = SymbolTable()
        i = self.buildInterpreter()
        i.setSymbolTable(st)
        self.assertEquals(i.environment.symbolTable,st)
        self.assertEquals(i.modes['ur'].__class__,UrMode)
        self.assertEquals(i.modes['staticSite'].__class__,StaticSiteMode)
        self.assertEquals(i.modes['html'].__class__,HtmlMode)
        self.assertEquals(i.modes['htmlForm'].__class__,HtmlFormMode)
        self.assertEquals(i.modes['ur'].getMode('html').__class__,HtmlMode)
        self.assertEquals(i.modes['htmlForm'].getMode('staticSite').__class__,StaticSiteMode)
        self.assertEquals(i.modes['ur'].getMode('inter').__class__,PhpMode)
        self.assertEquals(i.modes['javascript'].__class__,JavascriptMode)
        self.assertEquals(i.modes['data'].__class__,DataMode)        


    def testSomeSimpleStuff(self) :
        t = GWNode('.<p>').addChild(GWNode('blah blah blah'))
        i = self.buildInterpreter()
        self.assertEquals(i.evalNode(t,'html'),'<p>blah blah blah</p>')
        t = GWNode('.<p>').addChild(t)
        self.assertEquals(i.evalNode(t,'html'),'<p><p>blah blah blah</p></p>')
        
        
    def testSiteMapper(self) :
        sm = SiteMapper(Logger())
        sm.add('ttest/site','hello.html','Hello','hello world')
        sm.add('ttest/site','goodbye.html','Goodbye','porkpie')
        sm.add('ttest/site/deeper','sm.html','sm','here will $siteMap be')
        sm.addExternalLink('ttest/site/deeper','http://www.synaesmedia.net','Synaesmedia')
        self.assertEquals(sm.getDir('ttest/site'),[['ttest/site','hello.html','Hello'],['ttest/site','goodbye.html','Goodbye']])
        self.assertEquals(sm.getULIndex('ttest/site'),"""
<ul>
<li><a href='hello.html'><img border='0' src='ttest/site/dTree/img/folder.gif'/>&nbsp;Hello</a></li>
<li><a href='goodbye.html'><img border='0' src='ttest/site/dTree/img/folder.gif'/>&nbsp;Goodbye</a></li>
</ul>""")                 
        sm.writeAll({'siteMap':'XYZ'})

    def testEvalSiteNodes(self) :
        i = self.buildInterpreter()
        st = i.getSymbolTable()
        self.assertEquals(st.__class__,SymbolTable)
        st.pushFrame({"name" : "phil"})
        self.assertEquals(i.modes['ur'].evalSymbols('hello world',nullFellowTraveller()),'hello world')
        self.assertEquals(i.modes['ur'].evalSymbols('hello $name',nullFellowTraveller()),'hello phil')
        self.assertEquals(i.modes['ur'].evalSymbols('hello ${name}zinho',nullFellowTraveller()),'hello philzinho')

        
if __name__ == '__main__' :
    unittest.main()
