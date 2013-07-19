import searchEngine

__author__ = 'Artanis'

# pagelist = ['http://kiwitobes.com/wiki/Perl.html']
# crawler = searchEngine.crawler('')
# crawler.crawl(pagelist)

# crawler = searchEngine.crawler('SearchIndex.db')
# crawler.createIndexTables()
# pages = ['http://kiwitobes.com/wiki/Categorical_list_of_programming_languages.html']
# crawler.crawl(pages)

# result = [row for row in crawler.conn.execute("select urlId from WordLocation where wordId=1 order by urlId")]
# print len(result), result

result = searchEngine.Searcher('SearchIndex.db').getMatchRows("functional programming")[0]
print len(result), result