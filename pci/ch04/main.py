import searchEngine

__author__ = 'Artanis'

pagelist = ['http://kiwitobes.com/wiki/Perl.html']
crawler = searchEngine.crawler('')
crawler.crawl(pagelist)