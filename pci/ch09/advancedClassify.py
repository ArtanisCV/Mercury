from pylab import *
from svm import *
from svmutil import *
import math

__author__ = 'Artanis'


class MatchRow:
    def __init__(self, row, allNum=False):
        if allNum:
            self.data = [float(row[i]) for i in range(len(row) - 1)]
        else:
            self.data = row[0: -1]

        self.match = int(row[-1])


def loadMatch(fileName, allNum=False):
    rows = []

    for line in file(fileName):
        rows.append(MatchRow(line.strip().split(','), allNum))

    return rows


def plotAgeMatches(rows):
    xdm, ydm = [row.data[0] for row in rows if row.match == 1], \
               [row.data[1] for row in rows if row.match == 1]

    xdn, ydn = [row.data[0] for row in rows if row.match == 0], \
               [row.data[1] for row in rows if row.match == 0]

    plot(xdm, ydm, 'go')
    plot(xdn, ydn, 'rx')

    show()


def linearTrain(rows):
    averages = {}
    counts = {}

    for row in rows:
        # Get the class of this point
        match = row.match

        averages.setdefault(match, [0.0] * len(row.data))
        counts.setdefault(match, 0)

        # Add this point to the averages
        for i in range(len(row.data)):
            averages[match][i] += row.data[i]

        # Keep track of how many points in each class
        counts[match] += 1

    for match, avgData in averages.items():
        for i in range(len(avgData)):
            avgData[i] /= counts[match]

    return averages


def dotProduct(v1, v2):
    return sum([v1[i] * v2[i] for i in range(len(v1))])


def dpClassfy(point, avgs):
    b = (dotProduct(avgs[1], avgs[1]) - dotProduct(avgs[0], avgs[0])) / 2.0
    y = dotProduct(point, avgs[0]) - dotProduct(point, avgs[1]) + b

    if y > 0:
        return 0
    else:
        return 1


def yesNo(v):
    if v == 'yes':
        return 1
    elif v == 'no':
        return -1
    else:
        return 0


def matchCount(interest1, interest2):
    l1 = interest1.split(':')
    l2 = interest2.split(':')
    count = 0

    for v in l1:
        if v in l2:
            count += 1

    return count


yahooKey = ".rV1U9PV34FBSMSCenI_8QYvdYGbbGiUrWUSS5H.A91fCn1bM7FGrpNP7zLPCuen"
loc_cache = {}


def getLocation(address):
    if address in loc_cache:
        return loc_cache[address]

    from xml.dom.minidom import parseString
    from urllib import urlopen, quote_plus

    data = urlopen('http://local.yahooapis.com/MapsService/V1/' +
                   'mapImage?appid=%s&location=%s' %
                   (yahooKey, quote_plus(address))).read()
    doc = parseString(data)
    latitude = doc.getElementsByTagName('Latitude')[0].firstChild.nodeValue
    longtitude = doc.getElementsByTagName('Longitude')[0].firstChild.nodeValue

    loc_cache[address] = (float(latitude), float(longtitude))
    return loc_cache[address]


def milesDistance(addr1, addr2):
    #lat1, long1 = getLocation(addr1)
    #lat2, long2 = getLocation(addr2)
    #
    #latDiff = 69.1 * (lat2 - lat1)
    #longDiff = 53.0 * (long2 - long1)
    #return (latDiff ** 2 + longDiff ** 2) ** 0.5
    return 0.0


def loadNumerical():
    oldRows = loadMatch('matchMaker.csv')
    newRows = []

    for row in oldRows:
        oldData = row.data
        newRow = [float(oldData[0]), yesNo(oldData[1]), yesNo(oldData[2]),
                  float(oldData[5]), yesNo(oldData[6]), yesNo(oldData[7]),
                  matchCount(oldData[3], oldData[8]),
                  milesDistance(oldData[4], oldData[9]),
                  row.match]
        newRows.append(MatchRow(newRow))

    return newRows


def scaleData(rows):
    low = [999999999.0] * len(rows[0].data)
    high = [-999999999.0] * len(rows[0].data)

    # Find the lowest and highest values
    for row in rows:
        data = row.data

        for i in range(len(data)):
            if data[i] < low[i]:
                low[i] = data[i]
            if data[i] > high[i]:
                high[i] = data[i]

    # Create a function that scales data
    def scaleInput(data):
        scaled = []

        for i in range(len(data)):
            if low[i] == high[i]:
                scaled.append(0.0)
            else:
                scaled.append((data[i] - low[i]) / (high[i] - low[i]))

        return scaled

    # Scale all the data
    newRows = [MatchRow(scaleInput(row.data) + [row.match])
               for row in rows]

    # Return the new data and the function
    return newRows, scaleInput


def vecLength(v):
    return sum([p ** 2 for p in v])


def rbf(v1, v2, gamma=20):
    diff = [v1[i] - v2[i] for i in range(len(v1))]
    return math.e ** (-gamma * vecLength(diff))


def nlClassify(point, rows, offset, gamma=10):
    sum0 = 0.0
    sum1 = 0.0
    count0 = 0
    count1 = 0

    for row in rows:
        dist = rbf(point, row.data, gamma)

        if row.match == 0:
            sum0 += dist
            count0 += 1
        else:
            sum1 += dist
            count1 += 1

    y = sum0 / count0 - sum1 / count1 + offset

    if y < 0:
        return 1
    else:
        return 0


def getOffset(rows, gamma=10):
    l0 = []
    l1 = []

    for row in rows:
        if row.match == 0:
            l0.append(row.data)
        else:
            l1.append(row.data)

    sum0 = sum([sum([rbf(v1, v2, gamma) for v1 in l0]) for v2 in l0])
    sum1 = sum([sum([rbf(v1, v2, gamma) for v1 in l1]) for v2 in l1])

    return sum1 / float(len(l1) ** 2) - sum0 / float(len(l0) ** 2)


def testAdvancedClassify():
    agesOnly = loadMatch('agesOnly.csv', allNum=True)

    plotAgeMatches(agesOnly)

    avgs = linearTrain(agesOnly)

    print dpClassfy([30, 30], avgs)
    print dpClassfy([30, 25], avgs)
    print dpClassfy([25, 40], avgs)
    print dpClassfy([48, 20], avgs)

    #print
    #print getLocation('1 alewife center, cambridge, ma')
    #print milesDistance('cambridge, ma', 'new york,ny')

    print
    numericalSet = loadNumerical()
    print numericalSet[0].data

    print
    scaledSet, scaleF = scaleData(numericalSet)
    avgs = linearTrain(scaledSet)
    print numericalSet[0].data
    print numericalSet[0].match
    print dpClassfy(scaleF(numericalSet[0].data), avgs)
    print numericalSet[11].match
    print dpClassfy(scaleF(numericalSet[11].data), avgs)

    print
    offset = getOffset(agesOnly)
    print offset
    print nlClassify([30, 30], agesOnly, offset)
    print nlClassify([30, 25], agesOnly, offset)
    print nlClassify([25, 40], agesOnly, offset)
    print nlClassify([48, 20], agesOnly, offset)

    print
    offset = getOffset(scaledSet)
    print numericalSet[0].match
    print nlClassify(scaleF(numericalSet[0].data), scaledSet, offset)
    print numericalSet[1].match
    print nlClassify(scaleF(numericalSet[1].data), scaledSet, offset)
    print numericalSet[2].match
    print nlClassify(scaleF(numericalSet[2].data), scaledSet, offset)
    newRow = [28.0, -1, -1, 26.0, -1, 1, 2, 0.8]  # Man doesn't want children, woman does
    print nlClassify(scaleF(newRow), scaledSet, offset)
    newRow = [28.0, -1, 1, 26.0, -1, 1, 2, 0.8]  # Both want children
    print nlClassify(scaleF(newRow), scaledSet, offset)

    print
    problem = svm_problem([1, -1], [[1, 0, 1], [-1, 0, -1]])
    param = svm_parameter('-t 0 -c 10')
    model = svm_train(problem, param)

    print
    print svm_predict([1], [[1, 1, 1]], model)[0]

    print
    svm_save_model('test.model', model)
    print svm_predict([1], [[1, 1, 1]], svm_load_model('test.model'))[0]

    print
    answers, inputs = [row.match for row in scaledSet], [row.data for row in scaledSet]
    problem = svm_problem(answers, inputs)
    param = svm_parameter('-t 2')
    model = svm_train(problem, param)

    print
    newRow = [28.0, -1, -1, 26.0, -1, 1, 2, 0.8]  # Man doesn't want children, woman does
    print svm_predict([0], [scaleF(newRow)], model)[0]
    newRow = [28.0, -1, 1, 26.0, -1, 1, 2, 0.8]  # Both want children
    print svm_predict([1], [scaleF(newRow)], model)[0]

    print
    param.cross_validation = 4
    svm_train(problem, param)