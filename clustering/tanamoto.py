# -*- coding: utf-8 -*-
"""
Created on Sun Apr  3 17:43:49 2016

@author: Alex
"""

#define tanimoto coefficiant (like the pearson coefficiant but for binary values)
def tanamoto(v1,v2):
    c1,c2,shr=0,0,0
    
    for i in range(len(v1)):
        if v1[i]!=0: c1+=1 #in v1
        if v2[i]!=0: c2+=1 #in v2
        if v1[i]!=0 and v2[i]!=0: shr+=1 #in both
        
    return 1.0-(float(shr)/(c1+c2-shr))
    
#can use the hcluster function from clusters.py. we use the tanonoto distance metric instead of the pearson metric
#reload(clusters)
#wants,people,data=clusters.readfile('zebo.txt')
#clust=clusters.hcluster(data,distance=tanamoto)
#clusters.drawdendrogram(clust,wants)