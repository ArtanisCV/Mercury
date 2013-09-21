import zipfile
import time

__author__ = 'Artanis'


def loadMovieLens(path='MovieLens\ml-100k.zip'):
    movies = {}
    prefs = {}
    file = zipfile.ZipFile(path)

    for line in file.read('ml-100k/u.item').splitlines():
        (id, title) = line.split('|')[0:2]
        movies[id] = title

    for line in file.read('ml-100k/u.data').splitlines():
        (userId, movieId, rating, timestamp) = line.split('\t')
        prefs.setdefault(userId, {})
        prefs[userId][movies[movieId]] = float(rating)

    return prefs


def testMovieLens():
    import recommendations

    prefs = loadMovieLens()

    userId = '87'
    print prefs[userId]

    start = time.clock()
    print recommendations.getRecommendations(prefs, userId)[0:30]
    print "Total Time:" + str(time.clock() - start)
    print

    print "Preprocessing..."
    itemMatches = recommendations.calculateSimilarItems(prefs, n=50)
    print

    start = time.clock()
    print recommendations.getRecommendedItems(prefs, itemMatches, userId)[0:30]
    print "Total Time:" + str(time.clock() - start)
