import urllib2
from BeautifulSoup import *
from urlparse import urljoin

__author__ = 'Artanis'


# Create a list of words to ignore
ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])


class crawler:
    # Initialize the crawler with the name of database
    def __init__(self, dbname):
        pass

    def __del__(self):
        pass

    def dbCommit(self):
        pass

    # Auxilliary function for getting an entry id and adding
    # it if it's not present
    def getEntryId(self, table, field, value, createNew=True):
        return None

    # Index an individual page
    def addToIndex(self, url, soup):
        print 'Indexing %s' % url

    # Extract the text from an HTML page (no tags)
    def getTextOnly(self, soup):
        return None

    # Separate the words by any non-whitespace character
    def separateWords(self, text):
        return None

    # Return true if this url is already indexed
    def isIndexed(self, url):
        return False

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
        pass
