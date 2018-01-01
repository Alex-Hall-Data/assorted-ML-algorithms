# -*- coding: utf-8 -*-
"""
Created on Wed May 18 21:05:14 2016

@author: Alex

DOCUMENT CLASSIFIER - PROBABLY BETTER DONE IN RAPIDMINER THESE DAYS
"""

import re
import math

#function to extract features from text
def getwords(doc):
    splitter=re.compile('\\W*')
    #split the words by non-alpha characters
    words=[s.lower() for s in splitter.split(doc) if len(s)>2 and len(s)<20]
    
    #return unique set of words only
    return dict([(w,1) for w in words])
    
    
class classifier:
    def __init__(self,getfeatures,filename=None):
        #counts of feature/category combinations
        self.fc={}#stores counts for each feature in different classifications
        #counts of documents in each category
        self.cc={}#dictionary of how many times each classification has been used
        self.getfeatures=getfeatures#function used to extract features
        
    #increase the count of a feature/category pair
    def incf(self,f,cat):
        self.fc.setdefault(f,{})
        self.fc[f].setdefault(cat,0)
        self.fc[f][cat]+=1
        
    #increase the count of a category
    def incc(self,cat):
        self.cc.setdefault(cat,0)
        self.cc[cat]+=1
        
    #number of times a feature has appeared in a category
    def fcount(self,f,cat):
        if f in self.fc and cat in self.fc[f]:
            return float(self.fc[f][cat])
        return 0.0
        
    #the number of items in a category
    def catcount(self,cat):
        if cat in self.cc:
            return float(self.cc[cat])
        return 0
        
    #the total number of items
    def totalcount(self):
        return sum(self.cc.values())
        
    #the list of all categories
    def categories(self):
        return self.cc.keys()
    
    #method to take a document and a classification. breaks item into seperate features.
    #then increases counts for this classification for every feature using incf.
    #finally increases total count for this classification
    def train(self,item,cat):
        features=self.getfeatures(item)
        #increment the count for every feature with this category
        for f in features:
            self.incf(f,cat)
            
        #increment the count for this category
        self.incc(cat)
        
    #samples for trial training    
    def sampletrain(cl):
        cl.train('Nobody owns the water.','good')
        cl.train('the quick rabbit jumps fences','good')
        cl.train('buy pharmaceuticals now','bad')
        cl.train('make quick money at the online casino','bad')
        cl.train('the quick brown fox jumps','good')
        
    def fprob(self,f,cat):
        if self.catcount(cat)==0: return 0
        #the total number of times the feature has appeared in this category divided by the total number of items in the category
        #ie, conditional probability - for a given classification, gives the probability a given word appears
        return self.fcount(f,cat)/self.catcount(cat)
        
class naivebayes(classifier):
    def docprob(self,item,cat):
        features=self.getfeatures(item)
        
        #multiply the probabilities of all the features together
        p=1
        for f in features: p*=self.weightedprob(f,cat,self.ffprob):
        return p
     
    #returns P(Document\Category)*Pr(Category)  (using Bayes Theorum)
    def prob(self,item,cat):
        catprob=self.catcount(cat)/self.totalcount()
        docprob=self.docprob(item,cat)
        return docprob*catprob