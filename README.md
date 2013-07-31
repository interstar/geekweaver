GeekWeaver Templating Language
==============================


* Create templates in an outliner (OPML files)
  * One outline can compile to multiple pages
* Define your own re-usable "blocks" 
  * For menus, headers, etc.
  * Blocks also take parameters, so can be different on every page.
* Markdown support for easy HTML generation 
  * But GeekWeaver can be used to generate any kind of text file.



QuickStart 
----------
Make sure you have Python installed on your machine. ( http://python.org/ )

Also, ideally, you should also have Markdown

    easy_install markdown

GeekWeaver will work without Markdown support, but we now use it even for this quick-start demo. It's HIGHLY recommended.

    git clone https://github.com/interstar/geekweaver.git gw
    
    cd gw/quickstart/
    
    ./go.sh
    
    firefox demo/index.html
    

What did I just do?
-------------------
You grabbed a copy of GeekWeaver, went into the quickstart directory, ran the compiler on the demo file and looked at 
the result.

You should now see, in your browser a simple website created from a single GeekWeaver "program" ie. an OPML file.

It's in a frameset with a menu which lets you look at both the pages, and the logs of GeekWeaver compilation. 

You should also be able to find links to the source-code of these two pages.

The OPML file which contains the source is gwdemo.opml in the quickstart directory.

You can edit it using either http://fargo.io/ or the original OPML Editor ( http://home.opml.org/ )


