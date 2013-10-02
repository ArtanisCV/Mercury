import feedparser
import re

__author__ = 'Artanis'

feedList = ['http://today.reuters.com/rss/topNews',
            'http://today.reuters.com/rss/domesticNews',
            'http://today.reuters.com/rss/worldNews',
            'http://hosted.ap.org/lineups/TOPHEADS-rss_2.0.xml',
            'http://hosted.ap.org/lineups/USHEADS-rss_2.0.xml',
            'http://hosted.ap.org/lineups/WORLDHEADS-rss_2.0.xml',
            'http://hosted.ap.org/lineups/POLITICSHEADS-rss_2.0.xml',
            'http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'http://www.nytimes.com/services/xml/rss/nyt/International.xml',
            'http://news.google.com/?output=rss',
            'http://feeds.salon.com/salon/news',
            'http://www.foxnews.com/xmlfeed/rss/0,4313,0,00.rss',
            'http://www.foxnews.com/xmlfeed/rss/0,4313,80,00.rss',
            'http://www.foxnews.com/xmlfeed/rss/0,4313,81,00.rss',
            'http://rss.cnn.com/rss/edition.rss',
            'http://rss.cnn.com/rss/edition_world.rss',
            'http://rss.cnn.com/rss/edition_us.rss']


def stripHTML(html):
    p = ''
    s = 0

    for c in html:
        if c == '<':
            s = 1
        elif c == '>':
            s = 0
            p += ' '
        elif s == 0:
            p += c

    return p


def separateWords(text):
    splitter = re.compile(r'\W+')
    return [token.lower() for token in splitter.split(text) if len(token) > 3]


def getArticleWords():
    allWords = {}
    articleWords = []
    articleTitles = []
    ec = 0

    # Loop over every feed
    for feed in feedList:
        doc = feedparser.parse(feed)

        # Loop over every article
        for e in doc.entries:
            # Ignore identical articles
            if e.title in articleTitles:
                continue

            # Extract the words
            txt = e.title.encode('utf8') + stripHTML(e.description.encode('utf8'))
            words = separateWords(txt)
            articleWords.append({})
            articleTitles.append(e.title)

            # Increase the counts for this word in allWords and in articleWords
            for word in words:
                allWords.setdefault(word, 0)
                allWords[word] += 1
                articleWords[ec].setdefault(word, 0)
                articleWords[ec][word] += 1
            ec += 1

    return allWords, articleWords, articleTitles


def makeMatrix(allWords, articleWords):
    wordVec = []

    # Only take words that are common but not too common
    for word, count in allWords.items():
        if 3 < count < len(articleWords) * 0.6:
            wordVec.append(word)

    # Create the word matrix
    mat = [[(word in article and article[word] or 0) for word in wordVec]
           for article in articleWords]

    return mat, wordVec


def saveNews(allWords, articleWords, articleTitles):
    fd = open('news.txt', 'w')

    for word, count in allWords.items():
        fd.write(word + ' ' + str(count) + ' ')
    fd.write('\n')

    fd.write(str(len(articleWords)) + '\n')
    for wordCount in articleWords:
        for word, count in wordCount.items():
            fd.write(word + ' ' + str(count) + ' ')
        fd.write('\n')

    fd.write(str(len(articleTitles)) + '\n')
    for title in articleTitles:
        fd.write(title + '\n')

    fd.close()


def loadNews():
    allWords = {}
    articleWords = []
    articleTitles = []

    fd = open('news.txt', 'r')

    line = fd.readline()
    tokens = line.strip().split(' ')
    for i in range(0, len(tokens), 2):
        allWords[tokens[i]] = int(tokens[i + 1])

    line = fd.readline()
    nArticle = int(line)
    for i in range(nArticle):
        line = fd.readline()
        tokens = line.strip().split(' ')
        wordCount = {}
        for j in range(0, len(tokens), 2):
            wordCount[tokens[j]] = int(tokens[j + 1])
        articleWords.append(wordCount)

    line = fd.readline()
    nTitle = int(line)
    for i in range(nTitle):
        articleTitles.append(fd.readline().strip())

    fd.close()

    return allWords, articleWords, articleTitles


def testNewsFeatures():
    # allWords, articleWords, articleTitles = getArticleWords()
    # saveNews(allWords, articleWords, articleTitles)
    allWords, articleWords, articleTitles = loadNews()

    wordMatrix, wordVec = makeMatrix(allWords, articleWords)
    print wordVec[0: 10]
    print articleTitles[1]
    print wordMatrix[1][0: 10]

    def wordMatrixFeatures(counts):
        return [wordVec[i] for i in range(len(counts)) if counts[i] > 0]

    print
    print wordMatrixFeatures(wordMatrix[0])

    print
    from pci.ch06 import docClass

    classifier = docClass.NaiveBayes(wordMatrixFeatures)
    classifier.setDB('news.db')

    print articleTitles[0]
    # Train this as an 'government' story
    classifier.train(wordMatrix[0], 'government')

    print articleTitles[1]
    # Train this as an 'market' story
    classifier.train(wordMatrix[1], 'market')

    print articleTitles[2]
    # How is this story classified?
    print classifier.classify(wordMatrix[2])

    print
    from pci.ch03 import clusters

    clust = clusters.hCluster(wordMatrix)
    clusters.drawDendrogram(clust, articleTitles, jpeg='news.jpg')