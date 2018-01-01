# -*- coding: utf-8 -*-
"""
Created on Sat Apr  9 12:40:42 2016

@author: Alex
"""

import time
import random
import math

people=[('seymour','BOS'),('franny','DAL'),
        ('zooey','CAK'),('walt','MIA'),
        ('buddy','ORD'),('les','OMA')]
        
destination = 'LGA'

#load flight data in as dictionary
flights={}
for line in open('schedule.txt','r'):
    origin,dest,depart,arrive,price=line.strip().split(',')
    flights.setdefault((origin,dest),[])
    
    #add details to the list of possible flights
    flights[(origin,dest)].append((depart,arrive,int(price)))
    
#function to return time in minutes of given day
def getminutes(t):
    x=time.strptime(t,'%H:%M')
    return x[3]*60+x[4]
    
#simple fuction to convert list of flights into a readable table    
def printschedule(r):
    for d in range(int(len(r)/2)):
        name=people[d][0]
        origin=people[d][1]
        out=flights[(origin,destination)][r[d]]
        ret=flights[(destination,origin)][r[d+1]]
        print('%10s%10s %5s-%5s $%3s %5s-%5s $%3s' % (name,origin,out[0],out[1],out[2],ret[0],ret[1],ret[2]))
        
#the cost function - thisis what e are trying to optimise
#the parameters can be changed to give different weightings to different variables
def schedulecost(sol):
    totalprice=0
    latestarrival=0
    earliestdep=24*60
    
    for d in range(int(len(sol)/2)):
        #get in and outbound flights
        origin=people[d][1]
        outbound=flights[(origin,destination)][int(sol[d])]
        returnf=flights[(destination,origin)][int(sol[d+1])]
        
        #total price is price of all inbound and return flights
        totalprice+=outbound[2]
        totalprice+=returnf[2]
        
        #track the latest arrival and earliest departure
        if latestarrival<getminutes(outbound[1]): latestarrival=getminutes(outbound[1])
        if earliestdep>getminutes(returnf[0]): earliestdep=getminutes(returnf[0])
        
        #every person must wait at airport until latest person arrives (on outbound)
        #must also arrive at same time and wait for return flights
        totalwait=0
    for d in range(int(len(sol)/2)):
        origin=people[d][1]
        outbound=flights[(origin,destination)][int(sol[d])]
        returnf=flights[(destination,origin)][int(sol[d+1])]
        totalwait+=latestarrival-getminutes(outbound[1])
        totalwait+=getminutes(returnf[0])-earliestdep
            
    #add $50 if the solution requires an extra day of car rental
    if latestarrival>earliestdep: totalprice+=50
            
    return totalprice + totalwait
    
    
#random search (aka brute force). domain is the search space for each person
#this example only searches over 1000 solutions
def randomoptimise(domain,costf):
    best=999999999
    bestr=None
        #generate 1000 random solutions
    for i in range(1000):
            #generate a random solution
        r=[random.randint(domain[i][0],domain[i][1]) for i in range(len(domain))]
            #get the cost
        cost=costf(r)
            
            #compare to best so far
        if cost<best:
            best=cost
            bestr=r
    return bestr
    
#hill climbing algorithm
def hillclimb(domain, costf):
    #create a random solution
    sol=[random.randint(domain[i][0],domain[i][1]) for i in range(len(domain))]
    
    #main loop
    while 1:
        #create list of neighbouring solutions
        neighbours=[]
        for j in range(len(domain)):
            
            #one away in each direction
            if sol[j]>domain[j][0]:
                neighbours.append(sol[0:j]+[sol[j]+1]+sol[j+1:])
            if sol[j]<domain[j][1]:
                neighbours.append(sol[0:j]+[sol[j]-1]+sol[j+1:])
                
        #see what the best solution amongst the neighbours is
        current=costf(sol)
        best=current
        for j in range(len(neighbours)):
            cost=costf(neighbours[j])
            if cost<best:
                best=cost
                sol=neighbours[j]
                
        #if no improvement return solution
        if best==current:
            break
    return sol
    
def annealingoptimise(domain,costf,T=10000.0,cool=0.95,step=1):
    #initialise with a random solution
    vec=[float(random.randint(domain[i][0],domain[i][1])) for i in range(len(domain))]
    
    while T>0.1:
        #choose one of the indices
        i=random.randint(0,len(domain)-1)
    
        #choose a direction to change it
        dir=random.randint(-step,step)
        
        #create a new list with one of the values changed
        vecb=vec[:]
        vecb[i]+=dir
        if vecb[i]<domain[i][0]: vecb[i]=domain[i][0]
        elif vecb[i]>domain[i][1]: vecb[i]=domain[i][1]
            
        #calculate current cost and new cost
        ea=costf(vec)
        eb=costf(vecb)
        p=pow(math.e,(-eb-eb)/T)
        
        #is it better or does it make the probability cutoff?
        if(eb<ea or random.random()<p):
            vec=vecb
            
        #decrease the temperature
        T=T*cool
    return vec
    
#genetic algorithm
def geneticoptimise(domain,costf,popsize=50,step=1,mutprob=0.2,elite=0.2,maxiter=100):
    #mutation operation - changes a random element of the solution by 1
    def mutate(vec):
        i=random.randint(0,len(domain)-1)
        if random.random()<0.5 and vec[i]>domain[i][0]:
            return vec[0:i]+[vec[i]-step]+vec[i+1:]
        elif vec[i]<domain[i][1]:
            return vec[0:i]+[vec[i]+step]+vec[i+1:]
            
    #crossover (breeding) operation - combines random proportioms of 2 prior solutions
    def crossover(r1,r2):
        i=random.randint(1,len(domain)-2)
        return r1[0:i]+r2[i:]
        
    #build the initial population
    pop=[]
    for i in range(popsize):
        vec=[random.randint(domain[i][0],domain[i][1]) for i in range(len(domain))]
        pop.append(vec)
        
    #how many winners from each generation (ie how many to carry to next generation through elitism)
    topelite=int(elite*popsize)
    
    #main loop
    for i in range(maxiter):
        scores=[(costf(v),v) for v in pop]
        scores.sort()
        ranked=[v for (s,v) in scores]
        
        #start with the pure winners
        pop=ranked[0:topelite]
        
        #add mutated and bred forms of winners
        while len(pop)<popsize:
            if random.random()<mutprob:
                #generate a mutation
                c=random.randint(0,topelite)
                pop.append(mutate(ranked[c]))
            else:
                
                #crossover - pick 2 from elites:
                c1=random.randint(0,topelite)
                c2=random.randint(0,topelite)
                #cross them together and add to next generation
                pop.append(crossover(ranked[c1],ranked[c2]))
        #print current best score
        print(scores[0][0])
    return scores[0][1]