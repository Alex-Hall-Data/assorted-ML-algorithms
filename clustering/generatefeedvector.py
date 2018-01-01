import feedparser
import re

#return title and dictionary of word counts in an rss feed
def getwordcounts(url):
    #parse the feed
    d=feedparser.parse(url)
    wc={}

    #loop over all entries
    for e in d.entries:
        if 'summary' in e: summary=e.summary
        else: summary = e.description

        #extract a list of words
        words=getwords(e.title+' '+summary)
        for word in words:
            wc.setdefault(word,0)
            wc[word]+=1
        return d.feed.title,wc

def getwords(html):
    #remove all html tags
    txt=re.compile(r'<[^>]+>').sub('',html)

    #split the words by non-alphabetical characters
    words=re.compile(r'[^A-Z^a-z]+').split(txt)

    #convert to lowercase
    return[word.lower() for word in words if word!='']


#main code- loop over all urs in list of feeds and generate word dictionaries
apcount={}
wordcounts={}
for feedurl in open('feedlist.txt'):
    title,wc=getwordcounts(feedurl)
    wordcounts[title]=wc
    for word,count in wc.items():
        apcount.setdefault(word,0)
        if count>1:
            apcount[word]+=1

#remove 50% most common and 10% least common words
wordlist=[]
for w,bc in apcount.items():
    frac=float(bc)/len(apcount.items())
    if frac>0.1 and frac<0.5: wordlist.append(w)

#use the list of words and blogs to create matrix of word counts for each blog (in a text file)

out=open('blogdatawords.txt','w')
out.write('Blog')
for word in wordlist: out.write('\t%s' % word)
out.write('\n')
for blog, wc in wordcounts.items():
    out.write(blog)
    for word in wordlist:
        if word in wc: out.write('\t%d' % wc[word])
        else: out.write('\t0')
    out.write('\n')
