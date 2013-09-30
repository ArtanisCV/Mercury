from random import random, randint
from pylab import *
import math

__author__ = 'Artanis'


def winePrice(rating, age):
    peakAge = rating - 50
    price = rating / 2.0

    if age > peakAge:
        # Past its peak, goes bad in 5 years
        price *= 5 - (age - peakAge)
    else:
        # Increases to 5x original value as it approaches its peak
        price *= 5 * (age + 1) / peakAge

    if price < 0:
        price = 0

    return price


def wineSet1():
    rows = []

    for i in range(300):
        # Create a random age and rating
        rating = random() * 50 + 50
        age = random() * 50

        # Get reference price
        price = winePrice(rating, age)

        # Add some noise
        price *= random() * 0.4 + 0.8

        # Add to the dataset
        rows.append({'input': (rating, age), 'result': price})

    return rows


def euclidean(v1, v2):
    d = 0.0

    for i in range(len(v1)):
        d += (v1[i] - v2[i]) ** 2

    return math.sqrt(d)


def getDistances(data, vec):
    distances = []

    for i in range(len(data)):
        distances.append((euclidean(vec, data[i]['input']), i))

    distances.sort()
    return distances


def knnEstimate(data, vec, k=3):
    # Get sorted distances
    distances = getDistances(data, vec)
    avg = 0.0

    # Take the average of the top k results
    for i in range(k):
        idx = distances[i][1]
        avg += data[idx]['result']

    avg /= k
    return avg


def inverseWeight(dist, num=1.0, const=0.1):
    return num / (dist + const)


def substractWeight(dist, const=1.0):
    if dist > const:
        return 0
    else:
        return const - dist


def gaussian(dist, sigma=1.0):
    return math.e**(-dist**2 / (2 * sigma**2))


def weightedKnn(data, vec, k=5, weightF=gaussian):
    # Get sorted distances
    distances = getDistances(data, vec)
    avg = 0.0
    totalWeight = 0.0

    # Get weighted average
    for i in range(k):
        dist = distances[i][0]
        idx = distances[i][1]
        weight = weightF(dist)
        avg += weight * data[idx]['result']
        totalWeight += weight

    avg /= totalWeight
    return avg


def divideData(data, test=0.05):
    trainSet = []
    testSet = []

    for row in data:
        if random() < test:
            testSet.append(row)
        else:
            trainSet.append(row)

    return trainSet, testSet


def testAlgorithm(algF, trainSet, testSet):
    error = 0.0

    for row in testSet:
        guess = algF(trainSet, row['input'])
        error += (row['result'] - guess)**2

    return error / len(testSet)


def crossValidate(algF, data, trials=100, test=0.05):
    error = 0.0

    for i in range(trials):
        trainSet, testSet = divideData(data, test)
        error += testAlgorithm(algF, trainSet, testSet)

    return error / trials


def wineSet2():
    rows = []

    for i in range(300):
        rating = random() * 50 + 50
        age = random() * 50
        aisle = float(randint(1, 20))
        bottlesize = [375.0, 750.0, 1500.0, 3000.0][randint(0, 3)]
        price = winePrice(rating, age)
        price *= bottlesize / 750
        price *= random() * 0.9 + 0.2

        rows.append({'input': (rating, age, aisle, bottlesize), 'result': price})

    return rows


def rescale(data, scale):
    scaledData = []

    for row in data:
        scaled = [scale[i] * row['input'][i] for i in range(len(scale))]
        scaledData.append({'input': scaled, 'result': row['result']})

    return scaledData


def createCostFunction(algF, data):
    def costF(scale):
        sData = rescale(data, scale)
        return crossValidate(algF, sData, trials=10)

    return costF


def wineSet3():
    rows = wineSet1()

    for row in rows:
        if random() < 0.5:
            # Wine was bought at a discount store
            row['result'] *= 0.6

    return rows


def probGuess(data, vec, low, high, k=5, weightF=gaussian):
    distances = getDistances(data, vec)
    nWeight = 0.0
    tWeight = 0.0

    for i in range(k):
        dist = distances[i][0]
        idx = distances[i][1]
        weight = weightF(dist)
        price = data[idx]['result']

        # Is this point in the range?
        if low <= price <= high:
            nWeight += weight
        tWeight += weight

    if tWeight == 0:
        return 0

    # The probability is the weights in the range
    # divided by all the weights
    return nWeight / tWeight


def cumulativeGraph(data, vec, high, k=5, weightF=gaussian):
    t = arange(0.0, high, 0.1)
    cProb = array([probGuess(data, vec, 0, v, k, weightF) for v in t])
    plot(t, cProb)
    show()


def probabilityGraph(data, vec, high, k=5, weightF=gaussian, ss=5.0):
    # Make a range for the prices
    t = arange(0.0, high, 0.1)

    # Get the probabilities for the entire range
    probs = [probGuess(data, vec, v, v + 0.1, k, weightF) for v in t]

    # Smooth them by adding the gaussian fo the nearby probabilities
    smoothed = []
    for i in range(len(probs)):
        sv = 0.0

        for j in range(len(probs)):
            dist = abs(i - j) * 0.1
            weight = gaussian(dist, sigma=ss)
            sv += weight * probs[j]

        smoothed.append(sv)

    smoothed = array(smoothed)
    plot(t, smoothed)
    show()


def testNumPredict():
    print winePrice(95.0, 3.0)
    print winePrice(95.0, 8.0)
    print winePrice(99.0, 1.0)

    data = wineSet1()
    print data[0]
    print data[1]

    print
    print data[0]['input']
    print data[1]['input']
    print euclidean(data[0]['input'], data[1]['input'])

    print
    print knnEstimate(data, (95.0, 3.0))
    print knnEstimate(data, (99.0, 3.0))
    print knnEstimate(data, (99.0, 5.0))
    print winePrice(99.0, 5.0)
    print knnEstimate(data, (99.0, 5.0), k=1)

    print
    print substractWeight(0.1)
    print inverseWeight(0.1)
    print gaussian(0.1)
    print gaussian(1.0)
    print substractWeight(1.0)
    print inverseWeight(1.0)
    print gaussian(3.0)

    print
    print weightedKnn(data, (99.0, 5.0))

    print
    print crossValidate(lambda data, vec: knnEstimate(data, vec, k=5), data)
    print crossValidate(lambda data, vec: knnEstimate(data, vec, k=3), data)
    print crossValidate(lambda data, vec: knnEstimate(data, vec, k=1), data)
    print crossValidate(weightedKnn, data)
    print crossValidate(lambda data, vec: weightedKnn(data, vec, weightF=inverseWeight), data)

    print
    data = wineSet2()
    print crossValidate(knnEstimate, data)
    print crossValidate(weightedKnn, data)

    print
    sData = rescale(data, [1, 1, 0, 0.05])
    print crossValidate(knnEstimate, sData)
    print crossValidate(weightedKnn, sData)

    print
    weightDomain = [(0, 20)] * 4
    costF = createCostFunction(knnEstimate, data)
    from pci.ch05 import optimization
    print optimization.annealingOptimize(weightDomain, costF, step=2)
    print optimization.geneticOptimize(weightDomain, costF, popSize=5,
                                       step=1, elite=0.2, maxIter=20)

    print
    data = wineSet3()
    print winePrice(99.0, 20.0)
    print weightedKnn(data, [99.0, 20.0])
    print crossValidate(weightedKnn, data)

    print
    print probGuess(data, [99, 20], 40, 80)
    print probGuess(data, [99, 20], 80, 120)
    print probGuess(data, [99, 20], 120, 1000)
    print probGuess(data, [99, 20], 30, 120)

    a = array([1, 2, 3, 4])
    b = array([4, 2, 3, 1])
    plot(a, b)
    show()

    t = arange(0.0, 10.0, 0.1)
    plot(t, sin(t))
    show()

    cumulativeGraph(data, (99, 20), 160)

    probabilityGraph(data, (99, 20), 160)