__author__ = 'Artanis'

from data import critics
import recommendations

#print critics['Lisa Rose']

print recommendations.sim_euclidean(critics, 'Lisa Rose', 'Gene Seymour')

print recommendations.sim_pearson(critics, 'Lisa Rose', 'Gene Seymour')