# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 21:50:33 2016

@author: Alex
"""

from sqlite3 import dbapi2 as sqlite
from math import tanh

#gives differential if tanh so inputs are changes less the more the output is changes (see pg 80)      
def dtanh(y):
    return 1.0-y*y

class searchnet:
    def __init__(self,dbname):    
        self.con=sqlite.connect(dbname)
    
    def __del__(self):
        self.con.close()
        
#create tables for hidden nodes
    def maketables(self):
        self.con.execute('create table hiddennode(create_key)')
        self.con.execute('create table wordhidden(fromid,toid,strength)')
        self.con.execute('create table hiddenurl(fromid,toid,strength)')
        self.con.commit()
        
#method to determine current strength of a link. Default value from word to hidden node is -0.2 so extra words will have a slightly negative effect on activation of hidden node.
#default for links from hidden layer to urls is zero
    def getstrength(self,fromid,toid,layer):
        if layer==0: table='wordhidden'
        else: table='hiddenurl'
        res=self.con.execute('select strength from %s where fromid=%d and toid=%d' % (table, fromid, toid)).fetchone()
        if res==None:
            if layer==0: return -0.2
            if layer==1: return 0
        return res[0]
        
#method to determine whether a connection exists and to update with new strength
    def setstrength(self,fromid,toid,layer,strength):
        if layer==0: table='wordhidden'
        else: table='hiddenurl'
        res=self.con.execute('select rowid from %s where fromid=%d and toid=%d' % (table,fromid,toid)).fetchone()
        if res==None:
            self.con.execute('insert into %s (fromid,toid,strength) values (%d,%d,%f)' % (table,fromid,toid,strength))
        else:
            rowid=res[0]
            self.con.execute('update %s set strength=%f where rowid=%d' % (table,strength,rowid))
    
    #the NN creates a new hidden node every time it is given a combination of words it has not seen
    #this method creates the new node and creates default weighted links between the words and the hidden node and between the hidden node and output node (urls)
    
    def generatehiddennode(self,wordids,urls):
        if len(wordids)>3: return None
        #check whether we have already created a node for this set of words
        createkey='_'.join(sorted([str(wi) for wi in wordids])) #joins ords as a single string separated by '_'
        res=self.con.execute(" select rowid from hiddennode where create_key='%s'" %createkey).fetchone()
        
        #if not created, create the new hidden node
        if res==None:
            cur=self.con.execute("insert into hiddennode(create_key) values ('%s')" % createkey)
            hiddenid=cur.lastrowid
            #add default weights
            for wordid in wordids:
                self.setstrength(wordid,hiddenid,0,1.0/len(wordids))
            for urlid in urls:
                self.setstrength(hiddenid,urlid,1,0.1)
            self.con.commit()
            
            
    #find hidden nodes that are connected to the input words or the urls
    def getallhiddenids(self,wordids,urlids):
        l1={}
#get hidden nodes connected to input nodes    
        for wordid in wordids:
            cur=self.con.execute('select toid from wordhidden where fromid=%d' % wordid)
            for row in cur: l1[row[0]]=1
#get hidden nodes connected to output nodes       
        for urlid in urlids:
            cur=self.con.execute('select fromid from hiddenurl where toid=%d' % urlid)
            for row in cur: l1[row[0]]=1
        return list(l1) #changed to make python 3 compatible - http://stackoverflow.com/questions/17322668/typeerror-dict-keys-object-does-not-support-indexing
    
    
    #function to construct relevant network from using weights from the database. 
    def setupnetwork(self,wordids,urlids):
        #value lists
        self.wordids=wordids
        self.hiddenids=self.getallhiddenids(wordids,urlids)
        self.urlids=urlids
        
        #node outputs
        self.ai=[1.0]*len(self.wordids)
        self.ah=[1.0]*len(self.hiddenids)
        self.ao=[1.0]*len(self.urlids)
        
        #create matrix of weights from database using getstrength function
        self.wi=[[self.getstrength(wordid,hiddenid,0) for hiddenid in self.hiddenids] for wordid in self.wordids]
        #connections to output nodes
        self.wo=[[self.getstrength(hiddenid,urlid,1) for urlid in self.urlids] for hiddenid in self.hiddenids]
        
    #feedforward algorithm to take inputs and send them through network, returns output of all nodes in output layer
    #loops over all hidden nodes, adding togeth all the outputs from the input layer* the strengths of th links
    #output of each hidden node is tanh of the sum of the inputs
    #same for all output nodes (inputs in this case are the outputs of the hidden nodes)
    def feedforward(self):
        #inputs are query words
        for i in range(len(self.wordids)):
            #activate input nodes which correspond to the input words
            self.ai[i]=1.0
            
        #hidden activations
            #for all hidden nodes
        for j in range(len(self.hiddenids)):
            sum=0.0
            #for the ids of the input words
            for i in range(len(self.wordids)):
                #sum of links to the hidden node
                sum=sum+self.ai[i]*self.wi[i][j]
            #node responds to tanh of inputs
            self.ah[j]=tanh(sum)
            
        #output activations from hidden nodes
        for k in range(len(self.urlids)):
            sum=0.0
            for j in range(len(self.hiddenids)):
                sum=sum+self.ah[j]*self.wo[j][k]
            self.ao[k]=tanh(sum)
        return self.ao[:]

#call the above functions to return a result for input words
    def getresult(self,wordids,urlids):
        self.setupnetwork(wordids,urlids)
        return self.feedforward()
  
  
     #backpropogation method. Feedforward is run first to establish the output of every node in the instance variables then:
      #for the output layer:
      # calculate the difference between the nodes current output and what it should be
      #ue dtanh to determine how much the nodes input should change
      #change the strength of every incoming link in proportion to the links current strength and learning rate.
      #do essentially the same for the hidden layer
  
    def backpropogate(self,targets,N=0.5):
        #calculate errors for output
        #initialte list for all output nodes
        output_deltas=[0.0]*len(self.urlids)
        for k in range(len(self.urlids)):
            #error is target - actual
            error=targets[k]-self.ao[k]
            #change strength according to error*tanh(actual)
            output_deltas[k]=dtanh(self.ao[k])*error

        #calculate errors for hidden layer (as above)
        hidden_deltas=[0.0]*len(self.hiddenids)
        for j in range(len(self.hiddenids)):
            error=0.0
            for k in range(len(self.urlids)):
                error = error+output_deltas[k]*self.wo[j][k]
            hidden_deltas[j]=dtanh(self.ah[j])*error
            
        #update output weights
        for j in range(len(self.hiddenids)):
            for k in range(len(self.urlids)):
                change=output_deltas[k]*self.ah[j]
                self.wo[j][k]=self.wo[j][k]+N*change
                
        #update input weights
        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                change=hidden_deltas[j]*self.ai[i]
                self.wi[i][j]=self.wi[i][j]+N*change
                
        
        #method to take the above functions and set up network, run feedforward and run backpropogation.
        #this trains the nn
    def trainquery(self,wordids,urlids,selectedurl):
        #generate a hidden node if necessary
        self.generatehiddennode(wordids,urlids) #remember, the 'if' part is embedded in the generatehiddennode method
            
        self.setupnetwork(wordids,urlids)
        self.feedforward()
        targets=[0.0]*len(urlids)
        targets[urlids.index(selectedurl)]=1.0
        error=self.backpropogate(targets)
        self.updatedatabase()
            
        #method to save the results, pdating the database with the new weights
    def updatedatabase(self):
        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                self.setstrength(self.wordids[i],self.hiddenids[j],0,self.wi[i][j])
        for j in range(len(self.hiddenids)):
            for k in range(len(self.urlids)):
                self.setstrength(self.hiddenids[j],self.urlids[k],1,self.wo[j][k])
        self.con.commit()
            
            
        

            
            
    