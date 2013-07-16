from pci.ch2 import recommendations
from pci.ch2.data import critics

__author__ = 'Artanis'


# print critics['Lisa Rose']
# print
#
# print recommendations.sim_euclidean(critics, 'Lisa Rose', 'Gene Seymour')
# print recommendations.sim_pearson(critics, 'Lisa Rose', 'Gene Seymour')
# print
#
# print recommendations.topMatches(critics, 'Toby', n=3)
# print recommendations.getRecommendations(critics, 'Toby')
# print recommendations.getRecommendations(critics, 'Toby', similarity=recommendations.sim_euclidean)
# print
#
# movies = recommendations.transformPrefs(critics)
# print recommendations.topMatches(movies, 'Superman Returns')
# print recommendations.getRecommendations(movies, 'Just My Luck')
# print
#
# itemMatches = recommendations.calculateSimilarItems(critics)
# print itemMatches
# print recommendations.getRecommendedItems(critics, itemMatches, 'Toby')


# import delicious
#
# delicious.testDelicious()

import movieLens

movieLens.testMovieLens()

