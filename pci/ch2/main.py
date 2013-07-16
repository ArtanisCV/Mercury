from pci.ch2 import recommendations
from deliciousrec import testDelicious

__author__ = 'Artanis'

from pci.ch2.data import critics

print critics['Lisa Rose']
print

print recommendations.sim_euclidean(critics, 'Lisa Rose', 'Gene Seymour')
print recommendations.sim_pearson(critics, 'Lisa Rose', 'Gene Seymour')
print

print recommendations.topMatches(critics, 'Toby', n=3)
print recommendations.getRecommendations(critics, 'Toby')
print recommendations.getRecommendations(critics, 'Toby', similarity=recommendations.sim_euclidean)
print

movies = recommendations.transformPrefs(critics)
print recommendations.topMatches(movies, 'Superman Returns')
print recommendations.getRecommendations(movies, 'Just My Luck')
print

testDelicious()


