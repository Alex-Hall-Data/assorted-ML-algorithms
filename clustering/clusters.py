# -*- coding: utf-8 -*-
"""
Created on Sat Apr  2 16:26:50 2016

@author: Alex
"""
from math import sqrt
from PIL import Image, ImageDraw
import random

#read data file and return [blognames, words, data]
def readfile(filename):
    lines=[line for line in open(filename)]
    
    #first line is column titles
    colnames=lines[0].strip().split('\t')[1:]
    rownames=[]
    data=[]
    for line in lines[1:]:
        p=line.strip().split('\t')
        #first colun in each row is the rowname
        rownames.append(p[0])
        #the dta for this row is the remainder of the row
        data.append([float(x) for x in p[1:]])
    return rownames,colnames,data
    
def pearson(v1,v2):
    #sum
    sum1=sum(v1)
    sum2=sum(v2)
    
    #sum of squares
    sum1sq=sum([pow(v,2) for v in v1])
    sum2sq=sum([pow(v,2) for v in v2])
    
    #sum of the products
    psum=sum([v1[i]*v2[i] for i in range(len(v1))])
    
    #calculare pearson score (r)
    num = psum-(sum1*sum2/len(v1))
    den=sqrt((sum1sq-pow(sum1,2)/len(v1))*(sum2sq-pow(sum2,2)/len(v1)))
    if den==0: return 0
        
    return 1.0-num/den
 
#create a class to represent the hierachical tree   
class bicluster:
    def __init__(self,vec,left=None,right=None,distance=0.0,id=None):
        self.left=left
        self.right=right
        self.vec=vec
        self.id=id
        self.distance=distance
        
#HIERACHICAL CLUSTERING
#create clusters by repeatedly looping over items (see pg 36 paragraph 1 for explanation)
def hcluster(rows,distance=pearson):
    distances={}
    currentclustid=-1
    
    #clusters are initially the rows from the text file
    clust=[bicluster(rows[i],id=i) for i in range(len(rows))]
    
    while len(clust)>1:
        lowestpair=(0,1)
        closest=distance(clust[0].vec,clust[1].vec)
        
    #loop through each pair and find smallest distance
        for i in range(len(clust)):
            for j in range(i+1,len(clust)):
            #distances is the cache of distance calculations
                if (clust[i].id,clust[j].id) not in distances:
                    distances[(clust[i].id,clust[j].id)]=distance(clust[i].vec,clust[j].vec)
                
                d=distances[(clust[i].id,clust[j].id)]
            
                if d<closest:
                    closest=d
                    lowestpair=(i,j)
                
    
        #calculate the average values of the two clusters
        mergevec=[
        (clust[lowestpair[0]].vec[i]+clust[lowestpair[1]].vec[i])/2.0 for i in range(len(clust[0].vec))]
    
        #create the new cluster
        newcluster=bicluster(mergevec,left=clust[lowestpair[0]],right=clust[lowestpair[1]],distance=closest,id=currentclustid)
    
        #cluster ids that werent in the original set are negative
        currentclustid-=1
        del clust[lowestpair[1]]
        del clust[lowestpair[0]]
        clust.append(newcluster)
    
    return clust[0]

#note each cluster references the two merged to create it. Final cluster can be terefore searched recursivley to recreate all nodes

#function to print the hierachy tree
def printclust(clust,labels=None,n=0):
    #indent to make hierachy layout
    for i in range(n):
        print(' ')
    if clust.id<0:
        #negatie id means that this is branch
        print('-')
    else:
        #positive id means this is an endpoint
        if labels==None:
            print(clust.id)
        else:
            print(labels[clust.id])
            
    #print right and left branches
    if clust.left!=None: 
        printclust(clust.left,labels=labels,n=n+1)
    if clust.right!=None:
        printclust(clust.right,labels=labels,n=n+1)
        
#recursive function to get height of cluster
def getheight(clust):
    #if endpoint, height is 1
    if clust.left==None and clust.right==None: return 1
        
    #else, the height is the same as the heights of each branch
    return getheight(clust.left)+getheight(clust.right)
        
#get total error of thte root node
def getdepth(clust):
    #distance of an endpoint is zero
    if clust.left==None and clust.right==None: return 0
        #the distance of a branch is the greater of its two sides plus its own distance
    return max(getdepth(clust.left),getdepth(clust.right))+clust.distance
    
#function to draw dendrogram
def drawdendrogram(clust,labels,jpeg='clusters.jpg'):
    #height and width
    h=getheight(clust)*20
    w=1200
    depth=getdepth(clust)
    
    #width is fixed so scale distances accordingly
    scaling=float(w-150)/depth
    
    #create new image with white background
    img=Image.new('RGB',(w,h),(255,255,255))
    draw=ImageDraw.Draw(img)
    
    draw.line((0,h/2,10,h/2),fill=(255,0,0))
    
    #draw the first node
    drawnode(draw,clust,10,(h/2),scaling,labels)
    img.save(jpeg,'JPEG')
    
#Drawnode function to take a cluster and its location and draws lines to child nodes
def drawnode(draw,clust,x,y,scaling,labels):
    if clust.id<0:
        h1=getheight(clust.left)*20
        h2=getheight(clust.right)*20
        top=y-(h1+h2)/2
        bottom=y+(h1+h2)/2
        #line length
        ll=clust.distance*scaling
        #vertical line from cluster to children
        draw.line((x,top+h1/2,x,bottom-h2/2),fill=(255,0,0))
        
        #horizonal line o left item
        draw.line((x,top+h1/2,x+ll,top+h1/2),fill=(255,0,0))
        
        #horizontal line to right item
        draw.line((x,bottom-h2/2,x+ll,bottom-h2/2),fill=(255,0,0))
        
        #draw left and right nodes
        drawnode(draw,clust.left,x+ll,top+h1/2,scaling,labels)
        drawnode(draw,clust.right,x+ll,bottom-h2/2,scaling,labels)
    else:
        #if endpoint draw the item label
        draw.text((x+5,y-7),labels[clust.id],(0,0,0))

#function to rotate data so clustering is by word rather than by blog        
def rotatematrix(data):
    newdata=[]
    for i in range(len(data[0])):
        newrow=[data[j][i] for j in range(len(data))]
        newdata.append(newrow)
    return newdata
    
#to cluster by blog refer to pg 40 - apply rotatematrix to the data and apply clust function to rotated data. Then appy drawdendrogram


#K MEANS CLUSTERING
def kcluster(rows,distance=pearson,k=4):
    #determine minimum and maximum values for each point
    ranges=[(min([row[i] for row in rows]),max([row[i] for row in rows]))for i in range(len(rows[0]))]
        
    #create k randomly places centroids (minimum plus (min-max)*random is locatio of each centroid)
    clusters=[[random.random()*(ranges[i][1]-ranges[i][0])+ranges[i][0] for i in range(len(rows[0]))] for j in range(k)]
    
    lastmatches=None
    for t in range(100):
        print ('Iteration %d' %t)
        bestmatches=[[] for i in range(k)]
        
        #find which centroid is closest for each row
        for j in range(len(rows)):
            row=rows[j]
            bestmatch=0
            for i in range(k):
                d=distance(clusters[i],row)
                if d<distance(clusters[bestmatch],row): bestmatch=i
            bestmatches[bestmatch].append(j)
            
        #if results are the same as last time, don't need to iterate anymore
        if bestmatches==lastmatches: break
        lastmatches=bestmatches
        
        #move the centroids to the average of their members
        for i in range(k):
            avgs=[0.0]*len(rows[0])
            if len(bestmatches[i])>0:
                for rowid in bestmatches[i]:
                    for m in range(len(rows[rowid])):
                        avgs[m]+=rows[rowid][m]
                for j in range(len(avgs)):
                    avgs[j]/=len(bestmatches[i])
                clusters[i]=avgs
    
    return bestmatches
