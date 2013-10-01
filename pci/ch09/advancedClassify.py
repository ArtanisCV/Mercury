from pylab import *

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
    xdm, ydm = [row.data[0] for row in rows if row.match == 1],\
               [row.data[1] for row in rows if row.match == 1]

    xdn, ydn = [row.data[0] for row in rows if row.match == 0],\
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


def testAdvancedClassify():
    agesOnly = loadMatch('agesOnly.csv', allNum=True)
    matchMaker = loadMatch('matchMaker.csv')

    plotAgeMatches(agesOnly)