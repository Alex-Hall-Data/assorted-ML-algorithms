# -*- coding: utf-8 -*-
"""
Created on Sun Apr  3 20:37:45 2016

@author: Alex
"""
import sys
sys.setrecursionlimit(10000)#change recursion depth limit
import re
import urllib
from bs4 import *
from urllib.parse import urljoin
from urllib.request import urlopen as urlopen
#from sqlite3 import dbapi2 as sqlite

from sqlite3 import dbapi2 as sqlite
con=sqlite.connect('example10.db')

#get this bit into the crawler class and the script is identical to that in the textbook
#con.execute('create table urllist(url)')
#con.execute('create table wordlist(word)')
#con.execute('create table wordlocation(urlid,wordid,location)')
#con.execute('create table link(fromid integer, toid integer)')
#con.execute('create table linkwords(wordid, linkid)')
#con.execute('create index wordidx on wordlist(word)')
#con.execute('create index urlidx on urllist(url)')
#con.execute('create index wordurlidx on wordlocation(wordid)')
#con.execute('create index urltoidx on link(toid)')
#con.execute('create index urlfromidx on link(fromid)')
#con.commit()



#list of words to ignore
ignorewords=set(['the','of','to','and','a','in','is','it'])

class crawler:
    #initialise the crawler with the name of the databvse
    def __init__(self,dbname):
        self.con=sqlite.connect('example10.db')##FLAG - CHANGED THIS
    
    def __del__(self):
        self.con.close()
    def dbcommit(self):
        self.con.commit()
    

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

                

    
    #auzillary function for getting an entry id and adding if its not present
    def getentryid(self,table,field,value,createnew=True):
        cur=self.con.execute("select rowid from %s where %s='%s'" %(table,field,value))
#fetchone is an sql command to ftch the next row of the query set        
        res=cur.fetchone()
        if res==None:
            cur=self.con.execute("insert into %s (%s) values ('%s')" % (table,field,value))
            return(cur.lastrowid)
        else:
            return(res[0])
    
    #seperate the single string from above by any non whitespace character
    def seperatewords(self,text):
        splitter=re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s!='']
    
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
            self.con.execute("insert into wordlocation(urlid,wordid,location) values(%d,%d,%d)" %(urlid,wordid,i))
    
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
    

class searcher:
    def __init__(self,dbname):
        self.con=sqlite.connect(dbname)
        
    def __del__(self):
        self.con.close()
        
        #function to get indices of search words
    def getmatchrows(self,q):
        #strings to build the query
        fieldlist='w0.urlid'
        tablelist=''
        clauselist=''
        wordids=[]
        
        #split the words by spaces
        words=q.split(' ')
        tablenumber=0
        
        for word in words:
            #get the word id
            wordrow=self.con.execute(" select rowid from wordlist where word='%s'" % word).fetchone()
            if wordrow!=None:
                wordid=wordrow[0]
                wordids.append(wordid)
                if tablenumber>0:
                    tablelist+=','
                    clauselist+=' and '
                    clauselist+='w%d.urlid=w%d.urlid and ' % (tablenumber-1,tablenumber)
                fieldlist+=',w%d.location' % tablenumber
                tablelist+='wordlocation w%d' % tablenumber
                clauselist+='w%d.wordid=%d' % (tablenumber,wordid)
                tablenumber+=1
                
        #create the query from the seperate parts
        fullquery='select %s from %s where %s' % (fieldlist,tablelist,clauselist)
        cur=self.con.execute(fullquery)
        rows=[row for row in cur]
        
        return rows,wordids

            
    #rank results
    def getscoredlist(self,rows,wordids):
        totalscores=dict([(row[0],0) for row in rows])
        
        #scoring functions to go in here - change weighting by adjusting numbers
        weights=[(1.0,self.frequencyscore(rows)),(1.5,self.locationscore(rows)),(1,self.distancescore(rows))]
        
        for(weight,scores) in weights:
            for url in totalscores:
                totalscores[url]=weight*scores[url]
                
        return totalscores
        
    
    def geturlname(self,id):
        return self.con.execute("select url from urllist where rowid=%d" %id).fetchone()[0]
        
    def query(self,q):
        #get the indices of the resulting urls
        rows,wordids=self.getmatchrows(q)
        #get the scores
        scores=self.getscoredlist(rows,wordids)
        #rank the top 10 urls by their scores
        rankedscores=sorted([(score,url) for (url,score) in scores.items()],reverse=1)
        for(score,urlid) in rankedscores[0:10]:
            print ('%f\t%s' %(score,self.geturlname(urlid)))
      
#normalises scores between 0 and 1 regardles of scoring method used  (alo sccounts for direction since some methods give a small number for a better score)
#all scoring functions call this to normalise their scores
    def normalisedscores(self,scores,smallisbetter=0):
        vsmall=0.00001 #avoid division by zero
        if smallisbetter:
            minscore=min(scores.values())
            return dict([(u,float(minscore)/max(vsmall,l)) for (u,l) in scores.items()])
        else:
            maxscore=max(scores.values())
            if maxscore==0: maxscore=vsmall
                #reverses the order for metrics where a small value is better
            return dict([(u,float(c)/maxscore) for (u,c) in scores.items()])
  
#for all the below functions, 'rows' are the words found by query, with the corresponding word locations for each url   

#function to give score based on word frequncy.called by the weights row of the getscoredlist function      
    def frequencyscore(self,rows):
        counts=dict([(row[0],0) for row in rows])
        for row in rows: counts[row[0]]+=1
        return self.normalisedscores(counts)
        
#function to give score based on word location in document
    def locationscore(self,rows):
        #initialise the dictionary with large values
        #first item in each row element is urlid followed by locations of al the different search terms
        locations=dict([(row[0],1000000) for row in rows])
        for row in rows:
            #sums locations of all words and determines how this compares to the best result for that url
            loc=sum(row[1:])
            if loc<locations[row[0]]: locations[row[0]]=loc
                #url with lowest location sum gets a score of 1.0
        return self.normalisedscores(locations,smallisbetter=1)
        
#function to give score based on distance between searched words
    def distancescore(self,rows):
        #if only one word searched for, all urls win
        if len(rows[0])<=2: return dict([(row[0],1.0)for row in rows])
            
        #initialise the dictionary with large values
        mindistance=dict([(row[0],1000000) for row in rows])
        
        #for each url sum the distance between the words
        for row in rows:
        #loop through all locations and find distance between location and the previous - guaranteed to find the shortest
            dist=sum([abs(row[i]-row[i-1]) for i in range(2,len(row))])
            if dist<mindistance[row[0]]: mindistance[row[0]]=dist
        return self.normalisedscores(mindistance,smallisbetter=1)
        
#function to give score based on inbound links (like with an academi paper)
#not that useful by itself sinc bigger pages get more matches.Can also be manipulated
        def inboundlinkscore(self,rows):
            uniqueurls=set([row[0] for row in rows])
            #initialise dictionary of inbound links
            inboundcount=dict([(u,self.con.execute('select count(*) from link where toid=%d' %u).fetchone()[0]) for u in uniqueurls])
            return self.normalisedscores(inboundcount)