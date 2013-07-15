#!

# Released under the GNU General Public License, v3.0 or later
# Copyright (c) 2007 Phil Jones <interstar@gmail.com>

from libs.interpreter import *

version = '0.3.5'

if __name__ == '__main__' :
    fName = argv[1]
    oDir = argv[2]
    if len(argv) > 3 :
        packages = [argv[3]]
    else :
        packages = []
    print "GeekWeaver version %s" % version 
    print 'Copyright Phil Jones 2007-2013'
    print 'This code is released under the Gnu General Public License, version 3.0 or higher'

    f = InterpreterFactory()
    log = f.getLogger()

    print "Creating site from %s" % fName
    print "in directory %s" % oDir
    print "importing packages %s" % packages
  
    log.log('<h3>GeekWeaver version %s</h3>' % version,'html')
    log.log('<b>Copyright Phil Jones 2007-2013</b>','html')
    log.log('<i>This code is released under the Gnu General Public License, version 3.0 or higher</i>','html')
    log.log('Starting ...')
    i = f.getInterpreter()
    i.runFile(fName, oDir, packages)
    i.getLog().htmlFile('log.html')
    print 'Compilation finished'
