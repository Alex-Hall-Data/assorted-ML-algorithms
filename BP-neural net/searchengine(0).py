# -*- coding: utf-8 -*-
"""
Created on Sun Apr  3 20:37:45 2016

@author: Alex
"""

import urllib
from bs4 import *
from urllib.parse import urljoin
from urllib.request import urlopen as urlopen
#from sqlite3 import dbapi2 as sqlite
import sqlite3
conn = sqlite3.connect('example.db')#CHANGED THIS



#list of words to ignore
ignorewords=set(['the','of','to','and','a','in','is','it'])

class crawler:
    #initialise the crawler with the name of the databvse
    def __init__(self,dbname):
        self.con=sqlite3.connect(dbname)##FLAG - CHANGED THIS
    
    def __del__(self):
        self.con.close()
    def dbcommit(self):
        self.con.commit()
        

    
    #auzillary function for getting an entry id and adding if its not present
    def getentryid(self,table,field,value,createnew=True):
        cur=self.con.execute("select rowid from %s where %s='%s'" %(table,field,value))
#fetchone is an sql command to ftch the next row of the query set        
        res=cur.fetchone()
        if res==none:
            cur=self.con.execute("insert into %s (%s) values ('%s')" % (table,field,value))
            return(cur.lastrowid)
        else:
            return(res[0])
    
    #seperate the single string from above by any non whitespace character
    def separatewords(self,text):
        splitter=re.compile('\\w*')
        return[s.lower() for s in splitter.split(text) if s!='']
    
    #index an individual page
    def addtoindex(self,url,soup):
        if self.isindexed(url): return
        print('indexing %s' % url)
        
        #get the individual words
        text=self.gettextonly(soup)
        words=self.seperatewords(text)
        
        #get url id
        urlid=self.getentryid('urllist','url',url)
        
        #link each word to this url
        for i in range(len(words)):
            word=words[i]
            if word in ignorewords: continue
            wordid=self.getentryid('wordlist','word',word)
            self.con.execute("insert into wordlocation(urlid,wordid,location)\values(%d,%d,%d)" %(urlid,wordid,i))
    
    #extract the text from an html page as a single string(no tags)
    def gettextonly(self,soup):
        v=soup.string
        if v==None:
            c=soup.contents
            resulttext=''
#recursive function to traverse down HTML document, looking for text nodes.            
            for t in c:
                subtext=self.gettextonly(t)
                resulttext+=subtext+'\n'
            return resulttext
        else:
            #returns word stripped of whitespace characters (end of recursion)
            return v.strip()



        
    #return true if URL is already indexed
    def isindexed(self,url):
        u=self.con.execute\
            ("select rowid from urllist where url='%s'" % url).fetchone()
        if u!=None:
            #check if it has been crawled
            v=self.con.execute('select * from wordlocation where urlid=%d' %u[0]).fetchone()
            if v!=None: return(True)
        return(False)
        
    #add a link between two pages
    def addlinkref(self,urlfrom,urlto,linktext):
        pass
    
    #starting ith a list of pages do a breadth firt search to the given
    #depth, indexing pages as we go
    
    def crawl(self,pages,depth=2):
        for i in range(depth):
            newpages=set()
            for page in pages:
                try:
                    c=urlopen(page)
                except:
                    print ("Could not open %s" % page)
                    continue
                
                soup=BeautifulSoup(c.read())
                self.addtoindex(page,soup)
  
                links=soup('a')##CHANGED THIS
                for link in links:
                    if ('href' in dict(link.attrs)):
                        url=urljoin(page,link['href'])
                        if url.find("'")!=-1: continue
                        url=url.split('#')[0]  # remove location portion
                        if url[0:4]=='http' and not self.isindexed(url):
                            newpages.add(url)
                        linkText=self.gettextonly(link)
                        self.addlinkref(page,url,linkText)
  
                self.dbcommit()
                

            pages=newpages
    

    #create the new database tables
    def createindextables(self):
        self.con.execute('create table urllist(url)')
        self.con.execute('create table wordlist(word)')
        self.con.execute('create table wordlocation(urlid,wordid,location)')
        self.con.execute('create table link(fromid integer, toid integer)')
        self.con.execute('create table linkwords(wordid, linkid)')
        self.con.execute('create index wordidx on wordlist(word)')
        self.con.execute('create index urlidx on urllist(url)')
        self.con.execute('create index wordurlidx on wordlocation(wordid)')
        self.con.execute('create index urltoidx on link(toid)')
        self.con.execute('create index urlfromidx on link(fromid)')
        self.dbcommit()

            
    