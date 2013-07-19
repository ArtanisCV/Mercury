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
        handle = self.conn.execute("select rowId from %s where %s = '%s'" %
                                  (table, field, value))
        result = handle.fetchone()

        if result is None:
            if createNew:
                handle = self.conn.execute("insert into %s (%s) values ('%s')" %
                                          (table, field, value))
                return handle.lastrowid
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

        # Get the URL id
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
        pass

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
        self.conn.execute('create table UrlList(url)')
        self.conn.execute('create table WordList(word)')
        self.conn.execute('create table WordLocation(urlId, wordId, location)')
        self.conn.execute('create table Link(fromId integer, toId integer)')
        self.conn.execute('create table LinkWords(wordId, linkId)')
        self.conn.execute('create index WordIdx on WordList(word)')
        self.conn.execute('create index UrlIdx on UrlList(url)')
        self.conn.execute('create index WordUrlIdx on WordLocation(wordId)')
        self.conn.execute('create index urlToIdx on Link(toId)')
        self.conn.execute('create index urlFromIdx on Link(fromId)')
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