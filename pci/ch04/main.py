import searchEngine

__author__ = 'Artanis'


crawler = searchEngine.crawler('SearchIndex.db')

# crawler.createIndexTables()
#
# pages = ['http://kiwitobes.com/wiki/Categorical_list_of_programming_languages.html']
# crawler.crawl(pages)
# print [row for row in crawler.conn.execute("select urlId from WordLocation where wordId=1")]

# searcher = searchEngine.Searcher('SearchIndex.db')
#
# print searcher.getMatchRows("functional programming")[0]
# print searcher.query("functional programming")

# crawler.calculatePageRank()
# cursor = crawler.conn.execute('select * from PageRank order by score desc')
# for i in range(3):
#     print cursor.next()
# print searcher.getUrlName(438)

import neuralNetwork

myNet = neuralNetwork.searchNet('NeuralNetwork.db')

myNet.createTables()

wWorld, wRiver, wBank = 101, 102, 103
uWorldBank, uRiver, uEarth = 201, 202, 203
allUrlIds = [uWorldBank, uRiver, uEarth]

# myNet.generateHiddenNode([wWorld, wBank], allUrlIds)
# for c in myNet.conn.execute('select * from WordHidden'):
#     print c
# for c in myNet.conn.execute('select * from HiddenUrl'):
#     print c
#
# print myNet.getResult([wWorld, wBank], allUrlIds)

myNet.trainQuery([wWorld, wBank], allUrlIds, uWorldBank)
print myNet.getResult([wWorld, wBank], allUrlIds)

for i in range(30):
    myNet.trainQuery([wWorld, wBank], allUrlIds, uWorldBank)
    myNet.trainQuery([wRiver, wBank], allUrlIds, uRiver)
    myNet.trainQuery([wWorld], allUrlIds, uEarth)
print myNet.getResult([wWorld, wBank], allUrlIds)
print myNet.getResult([wRiver, wBank], allUrlIds)
print myNet.getResult([wBank], allUrlIds)

