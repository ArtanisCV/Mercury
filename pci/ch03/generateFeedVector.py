import re
import feedparser

__author__ = 'Artanis'


def getWords(html):
    # Remove all the HTML tags
    text = re.compile(r'<[^>]+>').sub('', html)

    # Split words by all non-alpha characters
    words = re.compile(r'[^A-Z^a-z]+').split(text)

    # Convert to lowercase
    return [word.lower() for word in words if word != '']


def getWordCounts(url):
    wc = {}

    try:
        doc = feedparser.parse(url)

        for entry in doc.entries:
            if 'summary' in entry:
                summary = entry.summary
            else:
                summary = entry.description

            for word in getWords(entry.title + ' ' + summary):
                wc.setdefault(word, 0)
                wc[word] += 1

        return doc.feed.title, wc
    except:
        return None


feedList = []
apCount = {}
docs = {}

for feedUrl in file('feedList.txt'):
    result = getWordCounts(feedUrl)

    if result is not None:
        feedList.append(feedUrl)

        title = result[0]
        wc = result[1]

        docs[title] = wc

        for (word, count) in wc.items():
            apCount.setdefault(word, 0)
            if count > 0:
                apCount[word] += 1

        print "Finish Processing Feed #" + str(len(feedList)) + "."


wordList = []

for (word, count) in apCount.items():
    frac = float(count) / len(feedList)

    if 0.1 < frac < 0.5:
        wordList.append(word)


out = file('blogData-tmp.txt', 'w')

out.write('Blog')
for word in wordList:
    out.write('\t%s' % word)
out.write('\n')

for (title, wc) in docs.items():
    out.write(title)
    for word in wordList:
        if word in wc:
            out.write('\t%d' % wc[word])
        else:
            out.write('\t0')
    out.write('\n')