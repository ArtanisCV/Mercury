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
        return 1 / (1 + (sum_of_square))


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


# Returns the best matches for person from the prefs dictionary.
# Number of results and similarity function are optional params.
def topMatches(prefs, person, n=5, similarity=sim_pearson):
    scores = [(similarity(prefs, person, other), other)
              for other in prefs if other != person]

    scores.sort()
    scores.reverse()
    return scores[0:n]


# Gets recommendations for a person by using a weighted average
# of every other user's rankings
def getRecommendations(prefs, person, similarity=sim_pearson):
    scores = {}
    simSums = {}

    for other in prefs:
        if other != person:
            sim = similarity(prefs, person, other)

            # ignore similarities of zero or lower
            if sim <= 0:
                continue

            for item in prefs[other]:

                # only score movies person haven't seen yet
                if item not in prefs[person] or prefs[person][item] == 0:
                    scores.setdefault(item, 0)
                    scores[item] += sim * prefs[other][item]

                    simSums.setdefault(item, 0)
                    simSums[item] += sim

    # Create the normalized list
    rankings = [(score / simSums[item], item)
                for (item, score) in scores.items()]

    rankings.sort()
    rankings.reverse()
    return rankings


# Flip items and persons
def transformPrefs(prefs):
    result = {}

    for person in prefs:
        for item in prefs[person]:
            result.setdefault(item, {})
            result[item][person] = prefs[person][item]

    return result


# Create a dictionary of items showing which other items they are most similar to.
def calculateSimilarItems(prefs, n=10):
    result = {}
    c = 0
    itemPrefs = transformPrefs(prefs)

    for item in itemPrefs:
        result[item] = topMatches(itemPrefs, item, n, sim_euclidean)

        # Status updates for large datasets
        c += 1
        if c % 100 == 0:
            print "%d / %d" % (c, len(itemPrefs))

    return result


def getRecommendedItems(prefs, itemMatches, user):
    userScores = prefs[user]
    scores = {}
    simSums = {}

    for (item1, rating) in userScores.items():
        for (similarity, item2) in itemMatches[item1]:

            # Ignore if this user has already rated this item
            if item2 not in userScores:
                scores.setdefault(item2, 0)
                scores[item2] += similarity * rating

                simSums.setdefault(item2, 0)
                simSums[item2] += similarity

    # Create the normalized list
    rankings = [(score / simSums[item], item)
                for (item, score) in scores.items()]

    rankings.sort()
    rankings.reverse()
    return rankings