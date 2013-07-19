import searchEngine

__author__ = 'Artanis'


crawler = searchEngine.crawler('SearchIndex.db')
# crawler.createIndexTables()
# pages = ['http://kiwitobes.com/wiki/Categorical_list_of_programming_languages.html']
# crawler.crawl(pages)

print [row for row in crawler.conn.execute("select urlId from WordLocation where wordId=1")]

searcher = searchEngine.Searcher('SearchIndex.db')
print searcher.getMatchRows("functional programming")[0]
print searcher.query("functional programming")
