from math import sqrt
import random
from PIL import Image, ImageDraw

__author__ = 'Artanis'


def readFile(filename):
    lines = [line for line in file(filename)]

    # First line is the column titles
    colNames = lines[0].strip().split('\t')[1:]

    rowNames = []
    data = []

    for line in lines[1:]:
        tokens = line.strip().split('\t')

        # First column in each row is the row title
        rowNames.append(tokens[0])

        # The data for this row is the remainder of the row
        data.append([float(token) for token in tokens[1:]])

    return rowNames, colNames, data


def pearson(v1, v2):
    n = len(v1)

    if len(v2) != n:
        return 1

    sum1 = sum(v1)
    sum2 = sum(v2)

    sumSq1 = sum([pow(v, 2) for v in v1])
    sumSq2 = sum([pow(v, 2) for v in v2])

    pSum = sum([v1[i] * v2[i] for i in range(n)])

    num = pSum - sum1 * sum2 / n
    den = sqrt((sumSq1 - pow(sum1, 2) / n) * (sumSq2 - pow(sum2, 2) / n))

    if den == 0:
        return 0
    else:
        # (1 - Pearson) creates a smaller distance between items that are more similar
        return 1 - num / den


def tanamoto(v1, v2):
    n = len(v1)
    nUnion = nInter = 0

    if len(v2) != n:
        return 1

    for i in range(n):
        if v1[i] != 0:
            nUnion += 1
            if v2[i] != 0:
                nInter += 1
        elif v2[i] != 0:
            nUnion += 1

    return 1.0 - float(nInter) / nUnion


class BiCluster:
    def __init__(self, vec, left=None, right=None, distance=0.0, id=None):
        self.vec = vec
        self.left = left
        self.right = right
        self.distance = distance
        self.id = id


# Hierarchical Clustering
def hCluster(vecs, distance=pearson):
    if len(vecs) == 0:
        return None

    cols = len(vecs[0])
    distances = {}
    currentClustId = -1

    # Clusters are initially just the rows
    clust = [BiCluster(vecs[i], id=i) for i in range(len(vecs))]

    while len(clust) > 1:
        lowestIdxPair = (0, 1)
        closest = distance(clust[0].vec, clust[1].vec)

        for i in range(len(clust)):
            for j in range(i + 1, len(clust)):
                idPair = (clust[i].id, clust[j].id)

                # distances is the cache of distance calculations
                if idPair not in distances:
                    distances[idPair] = distance(clust[i].vec, clust[j].vec)

                d = distances[idPair]

                if d < closest:
                    lowestIdxPair = (i, j)
                    closest = d

        # calculate the average of the two clusters
        mergeVec = [(clust[lowestIdxPair[0]].vec[i] + clust[lowestIdxPair[1]].vec[i]) / 2.0
                    for i in range(cols)]

        # create the new cluster
        newClust = BiCluster(vec=mergeVec, left=clust[lowestIdxPair[0]], right=clust[lowestIdxPair[1]],
                             distance=closest, id=currentClustId)

        # cluster ids that weren't in the original set are negative
        currentClustId -= 1

        del clust[lowestIdxPair[1]]
        del clust[lowestIdxPair[0]]
        clust.append(newClust)

    return clust[0]


def printClust(clust, labels=None, nIndent=0):
    # indent to make a hierarchy layout
    for i in range(nIndent):
        print ' ',

    if clust.id < 0:
        # negative id means that this is branch
        print '-'
    else:
        # positive id means that this is an endpoint
        if labels is None:
            print clust.id
        else:
            print labels[clust.id]

    # now print the right and left branches
    if clust.left is not None:
        printClust(clust.left, labels, nIndent + 1)
    if clust.right is not None:
        printClust(clust.right, labels, nIndent + 1)


def getHeight(clust):
    if clust is None:
        return 0
    elif (clust.left is None) and (clust.right is None):
        return 1
    else:
        return getHeight(clust.left) + getHeight(clust.right)


def getDepth(clust):
    if clust is None:
        return 0
    elif (clust.left is None) and (clust.right is None):
        return 0
    else:
        return max(getDepth(clust.left), getDepth(clust.right)) + clust.distance


def drawNode(draw, clust, x, y, scaling, labels):
    if clust.id < 0:
        h1 = getHeight(clust.left) * 20
        h2 = getHeight(clust.right) * 20
        top = y - (h1 + h2) / 2
        bottom = y + (h1 + h2) / 2

        # Line length
        ll = clust.distance * scaling

        # Vertical line from this cluster to children
        draw.line((x, top + h1 / 2, x, bottom - h2 / 2), fill=(255, 0, 0))

        # Horizontal line to left item
        draw.line((x, top + h1 / 2, x + ll, top + h1 / 2), fill=(255, 0, 0))

        # Horizontal line to right item
        draw.line((x, bottom - h2 / 2, x + ll, bottom - h2 / 2), fill=(255, 0, 0))

        # Call the function to draw the left and right nodes
        drawNode(draw, clust.left, x + ll, top + h1 / 2, scaling, labels)
        drawNode(draw, clust.right, x + ll, bottom - h2 / 2, scaling, labels)
    else:
        # If this is an endpoint, draw the item label
        draw.text((x + 5, y - 7), labels[clust.id], (0, 0, 0))


def drawDendrogram(clust, labels, jpeg='clusters.jpg'):
    # height and width
    h = getHeight(clust) * 20
    w = 1200
    depth = getDepth(clust)

    # width is fixed, so scale distances accordingly
    scaling = float(w - 150) / depth

    # Create a new image with a white background
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.line((0, h / 2, 10, h / 2), fill=(255, 0, 0))

    # Draw the first node
    drawNode(draw, clust, 10, (h / 2), scaling, labels)

    img.save(jpeg, 'JPEG')


def rotateMatrix(data):
    if len(data) == 0:
        return None

    nRow = len(data)
    nCol = len(data[0])
    newData = []

    for i in range(nCol):
        newData.append([data[j][i] for j in range(nRow)])

    return newData


def kCluster(vecs, k=4, distance=pearson):
    if len(vecs) == 0:
        return None

    cols = len(vecs[0])

    # Determine the minimum and maximum values for each column
    ranges = [(min([vec[i] for vec in vecs]), max([vec[i] for vec in vecs]))
              for i in range(cols)]

    # Create k randomly placed centroids
    centroids = [[random.random() * (ranges[i][1] - ranges[i][0]) + ranges[i][0] for i in range(cols)]
                 for j in range(k)]

    lastMatches = None
    for itr in range(100):
        print 'Iteration %d' % itr
        bestMatches = [[] for i in range(k)]

        for i in range(len(vecs)):
            vec = vecs[i]
            lowestIdx = 0
            closest = distance(vec, centroids[0])

            for j in range(1, k):
                d = distance(vec, centroids[j])

                if d < closest:
                    lowestIdx = j
                    closest = d

            bestMatches[lowestIdx].append(i)

        # If the results are the same as last time, this is complete
        if bestMatches == lastMatches:
            lastMatches = bestMatches
            break
        else:
            lastMatches = bestMatches

        # Move the centroids to the average of their members
        for i in range(k):
            nMatches = len(bestMatches[i])

            if nMatches > 0:
                centroids[i] = [sum([vecs[idx][j] for idx in bestMatches[i]]) / float(nMatches)
                                for j in range(cols)]

    return lastMatches


def scaleDown(data, distance=pearson, rate=0.01):
    if len(data) == 0:
        return None

    rows = len(data)
    cols = len(data[0])

    # The real distances between every pair of items
    expectedDist = [[distance(data[i], data[j]) for j in range(rows)]
                    for i in range(rows)]

    # Randomly initialize the starting points of the locations in 2D
    loc = [(random.random(), random.random()) for i in range(rows)]
    lastError = None

    def Euclidean(u, v):
        n = len(u)
        return sqrt(sum([pow(u[i] - v[i], 2) for i in range(n)]))

    for itr in range(1000):
        if itr % 100 == 0:
            print "Iteration %d" % itr

        # Find projected distances
        actualDist = [[Euclidean(loc[i], loc[j]) for j in range(rows)]
                      for i in range(rows)]

        # Move points
        grad = [(0.0, 0.0) for i in range(rows)]

        for i in range(rows):
            for j in range(rows):
                if i == j:
                    continue

                # The error is percent difference between the distances
                errorTerm = (actualDist[i][j] - expectedDist[i][j]) / expectedDist[i][j]

                # Each point needs to be moved away from or towards the other
                # point in proportion to how much error it has
