from math import sqrt
from PIL import Image, ImageDraw

__author__ = 'Artanis'


def readFile(filename):
    lines = [line for line in file(filename)]

    # First line is the column titles
    colNames = line[0].strip().split('\t')[1:]

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
        return 0

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


class BiCluster:
    def __init__(self, vec, left=None, right=None, distance=0.0, id=None):
        self.vec = vec
        self.left = left
        self.right = right
        self.distance = distance
        self.id = id


# Hierarchical Clustering
def hcluster(vecs, distance=pearson):
    if len(vecs) == 0:
        return None

    n = len(vecs[0])
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
                    for i in range(n)]

        # create the new cluster
        newClust = BiCluster(vec=mergeVec, left=clust[lowestIdxPair[0]], right=clust[lowestIdxPair[1]],
                             distance=closest, id=currentClustId)

        # cluster ids that weren't in the original set are negative
        currentClustId -= 1

        del clust[lowestIdxPair[1]]
        del clust[lowestIdxPair[0]]
        clust.append(newClust)

    return clust[0]


def printClust(clust, labels=None, n=0):
    # indent to make a hierarchy layout
    for i in range(n):
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
        printClust(clust.left, labels, n + 1)
    if clust.right is not None:
        printClust(clust.right, labels, n + 1)


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