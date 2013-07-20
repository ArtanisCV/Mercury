import urllib2
from BeautifulSoup import *
from urlparse import urljoin
from pysqlite2 import dbapi2 as sqlite

__author__ = 'Artanis'


# Create a list of words to ignore
ignoreWords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])


class crawler:
    # Initialize the crawler with the name of database
    def __init__(self, dbName):
        self.conn = sqlite.connect(dbName)

    def __del__(self):
        self.conn.close()

    def dbCommit(self):
        self.conn.commit()

    # Auxilliary function for getting an entry id and adding
    # it if it's not present
    def getEntryId(self, table, field, value, createNew=True):
        cursor = self.conn.execute("select rowId from %s where %s = '%s'" %
                                   (table, field, value))
        result = cursor.fetchone()

        if result is None:
            if createNew:
                cursor = self.conn.execute("insert into %s(%s) values ('%s')" %
                                           (table, field, value))
                return cursor.lastrowid
            else:
                return -1
        else:
            return result[0]

    # Index an individual page
    def addToIndex(self, url, soup):
        if self.isIndexed(url):
            return

        print 'Indexing %s' % url

        # Get the individual words
        text = self.getTextOnly(soup)
        words = self.separateWords(text)

        # Get the url id
        urlId = self.getEntryId('UrlList', 'url', url)

        # Link each word to this url
        for i in range(len(words)):
            if words[i] not in ignoreWords:
                wordId = self.getEntryId('WordList', 'word', words[i])

                self.conn.execute("insert into WordLocation(urlId, wordId, location) values (%d, %d, %d)" %
                                  (urlId, wordId, i))

    # Extract the text from an HTML page (no tags)
    def getTextOnly(self, soup):
        text = soup.string

        if text is None:
            text = ''

            for content in soup.contents:
                subText = self.getTextOnly(content)
                text += subText + '\n'

            return text
        else:
            return text.strip()

    # Separate the words by any non-whitespace character
    def separateWords(self, text):
        separators = re.compile('\\W*')
        return [word.lower() for word in separators.split(text) if word != '']

    # Return true if this url is already indexed
    def isIndexed(self, url):
        urlResult = self.conn.execute("select rowId from UrlList where url = '%s'" % url).fetchone()

        if urlResult is None:
            return False
        else:
            # Check if it has actually been crawled
            if self.conn.execute("select * from WordLocation where urlId = '%d'" % urlResult[0]).fetchone() is None:
                return False
            else:
                return True

    # Add a link between two pages
    def addLinkRef(self, urlFrom, urlTo, linkText):
        words = self.separateWords(linkText)
        fromId = self.getEntryId("UrlList", "url", urlFrom)
        toId = self.getEntryId("UrlList", "url", urlTo)

        if fromId == toId:
            return
        else:
            cursor = self.conn.execute("insert into Link(fromId, toId) values (%d, %d)" % (fromId, toId))
            linkId = cursor.lastrowid

            for word in words:
                if word not in ignoreWords:
                    wordId = self.getEntryId("WordList", "word", word)
                    self.conn.execute("insert into LinkWords(linkId, wordId) values (%d, %d)" % (linkId, wordId))

    # Starting with a list of urls, do a breadth
    # first search to the given depth, indexing pages
    # as we go
    def crawl(self, urls, depth=2):
        for i in range(depth):
            newUrls = set()

            for url in urls:
                try:
                    file = urllib2.urlopen(url)
                except:
                    print "Could not open %s" % url
                    continue

                soup = BeautifulSoup(file.read())
                self.addToIndex(url, soup)

                for link in soup('a'):
                    if 'href' in dict(link.attrs):
                        newUrl = urljoin(url, link['href'])

                        if newUrl.find("'") != -1:
                            print "Incorrect url: %s" % newUrl
                            continue

                        # remove location portion
                        newUrl = newUrl.split('#')[0]

                        if newUrl[0:4] == 'http' and not self.isIndexed(newUrl):
                            newUrls.add(newUrl)

                        linkText = self.getTextOnly(link)
                        self.addLinkRef(url, newUrl, linkText)

                self.dbCommit()

            urls = newUrls

    # Create the database tables
    def createIndexTables(self):
        self.conn.execute("drop table if exists UrlList")
        self.conn.execute("create table UrlList(url)")

        self.conn.execute("drop table if exists WordList")
        self.conn.execute("create table WordList(word)")

        self.conn.execute("drop table if exists WordLocation")
        self.conn.execute("create table WordLocation(urlId, wordId, location)")

        self.conn.execute("drop table if exists Link")
        self.conn.execute("create table Link(fromId integer, toId integer)")

        self.conn.execute("drop table if exists LinkWords")
        self.conn.execute("create table LinkWords(wordId, linkId)")

        self.conn.execute("drop index if exists WordIdx")
        self.conn.execute("create index WordIdx on WordList(word)")

        self.conn.execute("drop index if exists UrlIdx")
        self.conn.execute("create index UrlIdx on UrlList(url)")

        self.conn.execute("drop index if exists WordUrlIdx")
        self.conn.execute("create index WordUrlIdx on WordLocation(wordId)")

        self.conn.execute("drop index if exists UrlToIdx")
        self.conn.execute("create index UrlToIdx on Link(toId)")

        self.conn.execute("drop index if exists UrlFromIdx")
        self.conn.execute("create index UrlFromIdx on Link(fromId)")

        self.dbCommit()

    def calculatePageRank(self, iterations=20):
        # clear out the current PageRank tables
        self.conn.execute("drop table if exists PageRank")
        self.conn.execute("create table PageRank(urlId primary key, score)")

        # initialize every url with a PageRank of 1
        self.conn.execute("insert into PageRank select rowId, 1 from UrlList")
        self.dbCommit()

        for itr in range(iterations):
            print "Iteration %d" % itr

            for (urlId,) in self.conn.execute("select rowId from UrlList"):
                pageRank = 0.15

                # Loop through all the urls that link to this one
                for (inUrlId,) in self.conn.execute("select distinct fromId from Link where toId = %d" % urlId):
                    # Get the PageRank of the inUrl
                    inUrlPR = self.conn.execute("select score from PageRank where urlId = %d" % inUrlId).fetchone()[0]

                    # Get the total number of links from the inUrl
                    count = self.conn.execute("select count(*) from Link where fromId = %d" % inUrlId).fetchone()[0]

                    pageRank += 0.85 * inUrlPR / count

                self.conn.execute("update PageRank set score = %f where urlId = %d" % (pageRank, urlId))

            self.dbCommit()


class Searcher:
    def __init__(self, dbName):
        self.conn = sqlite.connect(dbName)

    def __del__(self):
        self.conn.close()

    def getMatchRows(self, query):
        # Strings to build the database query
        fieldList = 'wl0.urlId'
        tableList = ''
        clauseList = ''
        tableIdx = 0
        wordIds = []

        # Split the words by spaces
        for word in query.split(' '):
            # Get the word ID
            wordResult = self.conn.execute("select rowId from WordList where word = '%s'" % word).fetchone()

            if wordResult is not None:
                wordId = wordResult[0]
                wordIds.append(wordId)

                if tableIdx > 0:
                    tableList += ', '
                    clauseList += ' and wl%d.urlId = wl%d.urlId and ' % (tableIdx - 1, tableIdx)

                fieldList += ', wl%d.location' % tableIdx
                tableList += 'WordLocation wl%d' % tableIdx
                clauseList += 'wl%d.wordId = %d' % (tableIdx, wordId)
                tableIdx += 1

        # Create the query from the separate parts
        result = self.conn.execute("select %s from %s where %s" % (fieldList, tableList, clauseList))

        if result is None:
            return [], wordIds
        else:
            return [row for row in result], wordIds

    def getScoredList(self, rows, wordIds):
        totalScores = dict([(row[0], 0) for row in rows])

        weights = [(1.0, self.frequencyScore(rows)),
                   (1.0, self.locationScore(rows)),
                   #(1.0, self.distanceScore(rows)),
                   (1.0, self.pageRankScore(rows)),
                   (1.0, self.linkTextScore(rows, wordIds))]

        for (weight, scores) in weights:
            for urlId in totalScores:
                totalScores[urlId] += weight * scores[urlId]

        return totalScores

    def getUrlName(self, urlId):
        result = self.conn.execute("select url from UrlList where rowId = %d" % urlId).fetchone()

        if result is None:
            return None
        else:
            return result[0]

    def query(self, queryText):
        (rows, wordIds) = self.getMatchRows(queryText)
        scores = self.getScoredList(rows, wordIds)

        rankedScores = sorted([(score, urlId) for (urlId, score) in scores.items()], reverse=True)

        for (score, urlId) in rankedScores:
            print "%f\t%s" % (score, self.getUrlName(urlId))

        return wordIds, [urlId for (score, urlId) in rankedScores[0:10]]

    # return scores between 0 (the worst) and 1 (the best)
    def normalizeScores(self, scores, smallIsBetter=False):
        # Avoid division by zero errors
        eps = 0.00001

        if smallIsBetter:
            minScore = max(eps, min(scores.values()))
            return dict([(u, float(minScore) / max(eps, v)) for (u, v) in scores.items()])
        else:
            maxScore = max(eps, max(scores.values()))
            return dict([(u, float(v) / maxScore) for (u, v) in scores.items()])

    def frequencyScore(self, rows):
        counts = {}

        for row in rows:
            counts.setdefault(row[0], 0)
            counts[row[0]] += 1

        return self.normalizeScores(counts)

    def locationScore(self, rows):
        eps = 10000000
        locations = {}

        for row in rows:
            locations.setdefault(row[0], eps)
            locations[row[0]] = min(locations[row[0]], sum(row[1:]))

        return self.normalizeScores(locations, smallIsBetter=True)

    def distanceScore(self, rows):
        if len(rows) == 0:
            return {}

        eps = 10000000
        nWord = len(rows[0])
        distances = {}

        # If there's only one word, everyone wins!
        if nWord <= 2:
            return dict([(row[0], 1.0) for row in rows])

        for row in rows:
            distances.setdefault(row[0], eps)
            distances[row[0]] = min(distances[row[0]], sum([abs(row[i] - row[i - 1]) for i in range(2, nWord)]))

        return self.normalizeScores(distances, smallIsBetter=True)

    def inboundLinkScore(self, rows):
        urlIds = set([row[0] for row in rows])
        inboundCounts = {}

        for urlId in urlIds:
            inboundCounts[urlId] = self.conn.execute("select count(*) from Link where toId = %d" % urlId).fetchone()[0]

        return self.normalizeScores(inboundCounts)

    def pageRankScore(self, rows):
        pageRanks = dict(
            [(row[0], self.conn.execute("select score from PageRank where urlId = %d" % row[0]).fetchone()[0])
             for row in rows])

        return self.normalizeScores(pageRanks)

    def linkTextScore(self, rows, wordIds):
        linkTextScores = dict([(row[0], 0.0) for row in rows])

        for wordId in wordIds:
            cursor = self.conn.execute(
                "select Link.fromId, Link.toId from Link, LinkWords "
                "where Link.rowId = LinkWords.linkId and LinkWords.wordId = %d" % wordId)

            for (fromId, toId) in cursor:
                if toId in linkTextScores:
                    linkTextScores[toId] += \
                        self.conn.execute("select score from PageRank where urlId = %d" % fromId).fetchone()[0]

        return self.normalizeScores(linkTextScores)

    def neuralNetworkScore(self, rows, wordIds):
        import neuralNetwork

        # Get unique URL IDs as an ordered list
        urlIds = [urlId for urlId in set([row[0] for row in rows])]

        myNet = neuralNetwork.searchNet('NerualNetwork.db')
        result = myNet.getResult(wordIds, urlIds)

        scores = dict([(urlIds[i], result[i]) for i in range(len(urlIds))])
        return self.normalizeScores(scores)