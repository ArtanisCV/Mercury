from numpy import *
import os
import urllib2
import nmf

__author__ = 'Artanis'

dataDir = 'Finances'
tickers = ['YHOO', 'AVP', 'BIIB', 'BP', 'CL', 'CVX',
           'AAPL', 'EXPE', 'GOOG', 'PG', 'XOM', 'AMGN']

shortest = 300
prices = {}
dates = None

for t in tickers:
    # Load data
    dataPath = dataDir + os.sep + '%s.csv' % t

    if os.path.exists(dataPath):
        fd = open(dataPath, 'r')
        rows = fd.readlines()
        fd.close()
    else:
        rows = urllib2.urlopen('http://ichart.finance.yahoo.com/table.csv?' +
                               's=%s&d=11&e=26&f=2006&g=d&a=3&b=12&c=1996' % t +
                               '&ignore=.csv').readlines()

        fd = open(dataPath, 'w')
        fd.writelines(rows)
        fd.close()

    # Extract the volumn field from every line
    prices[t] = [float(row.split(',')[5]) for row in rows[1:] if row.strip() != '']

    if len(prices[t]) < shortest:
        shortest = len(prices[t])

    if not dates:
        dates = [row.split(',')[0] for row in rows[1:] if row.strip() != '']

list2d = [[prices[tickers[i]][j] for i in range(len(tickers))]
          for j in range(shortest)]


def testStockVolume():
    weights, features = nmf.factorize(matrix(list2d), 8)

    print weights
    print features

    print

    # Loop over all the features
    for i in range(features.shape[0]):
        print "Feature %d" % i

        # Get the top stocks for this feature
        topStocks = [(features[i, j], tickers[j]) for j in range(features.shape[1])]
        topStocks.sort()
        topStocks.reverse()

        for j in range(12):
            print topStocks[j]
        print

        # Show the top dates for this feature
        topDates = [(weights[d, i], d) for d in range(300)]
        topDates.sort()
        topDates.reverse()

        print [(item[0], dates[item[1]]) for item in topDates[0:3]]
        print
