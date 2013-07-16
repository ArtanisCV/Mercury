from math import sqrt

__author__ = 'Artanis'


# Returns an euclidean-distance-based similarity score for person1 and person2
def sim_euclidean(prefs, person1, person2):
    n = sum_of_square = 0

    for item in prefs[person1]:
        if item in prefs[person2]:
            sum_of_square += pow(prefs[person1][item] - prefs[person2][item], 2)
            n += 1

    # If they have no ratings in common, return 0
    if n == 0:
        return 0
    else:
        return 1 / (1 + sqrt(sum_of_square))


# Returns the Pearson correlation coefficient for person1 and person2
def sim_pearson(prefs, person1, person2):
    n = sum1 = sum2 = sumSq1 = sumSq2 = pSum = 0

    for item in prefs[person1]:
        if item in prefs[person2]:
            sum1 += prefs[person1][item]
            sum2 += prefs[person2][item]
            sumSq1 += pow(prefs[person1][item], 2)
            sumSq2 += pow(prefs[person2][item], 2)
            pSum += prefs[person1][item] * prefs[person2][item]
            n += 1

    # If they have no ratings in common, return 0
    if n == 0:
        return 0
    else:
        num = pSum - (sum1 * sum2 / n)
        den = sqrt((sumSq1 - pow(sum1, 2) / n) * (sumSq2 - pow(sum2, 2) / n))

        if den == 0:
            return 0
        else:
            return num / den