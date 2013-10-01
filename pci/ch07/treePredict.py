from math import log
from PIL import Image, ImageDraw

__author__ = 'Artanis'

userData = [['slashdot', 'USA', 'yes', 18, 'None'],
            ['google', 'France', 'yes', 23, 'Premium'],
            ['digg', 'USA', 'yes', 24, 'Basic'],
            ['kiwitobes', 'France', 'yes', 23, 'Basic'],
            ['google', 'UK', 'no', 21, 'Premium'],
            ['(direct)', 'New Zealand', 'no', 12, 'None'],
            ['(direct)', 'UK', 'no', 21, 'Basic'],
            ['google', 'USA', 'no', 24, 'Premium'],
            ['slashdot', 'France', 'yes', 19, 'None'],
            ['digg', 'USA', 'no', 18, 'None'],
            ['google', 'UK', 'no', 18, 'None'],
            ['kiwitobes', 'UK', 'no', 19, 'None'],
            ['digg', 'New Zealand', 'yes', 12, 'Basic'],
            ['slashdot', 'UK', 'no', 21, 'None'],
            ['google', 'UK', 'yes', 18, 'Basic'],
            ['kiwitobes', 'France', 'yes', 19, 'Basic']]


class DecisionNode:
    def __init__(self, col=-1, value=None, results=None, tB=None, fB=None):
        self.col = col
        self.value = value
        self.results = results
        self.tB = tB
        self.fB = fB


# Divides a set on a specific column. Can handle numeric
# or nominal values
def divideSet(rows, column, value):
    # Make a function that tells us if a row is in
    # the first group (true) or the second group (false)
    if isinstance(value, int) or isinstance(value, float):
        splitFunction = lambda row: row[column] >= value
    else:
        splitFunction = lambda row: row[column] == value

    # Divide the rows into two sets and return them
    set1 = [row for row in rows if splitFunction(row)]
    set2 = [row for row in rows if not splitFunction(row)]

    return set1, set2


# Create counts of possible results (the last column of
# each row is the result)
def uniqueCounts(rows):
    counts = {}

    for row in rows:
        # The result is the last column
        result = row[-1]
        counts.setdefault(result, 0)
        counts[result] += 1

    return counts


# Probability that a randomly placed item will
# be in the wrong category
def giniImpurity(rows):
    total = len(rows)
    counts = uniqueCounts(rows)
    imp = 0.0

    for k1 in counts:
        p1 = float(counts[k1]) / total

        for k2 in counts:
            if k1 == k2:
                continue

            p2 = float(counts[k2]) / total
            imp += p1 * p2

    return imp


# Entropy is the sum of p(x)log(p(x)) across all
# the different possible results
def entropy(rows):
    log2 = lambda x: log(x) / log(2.0)
    total = len(rows)
    counts = uniqueCounts(rows)
    ent = 0.0

    # Now calculate the entropy
    for k in counts:
        p = float(counts[k]) / total
        ent -= p * log2(p)

    return ent


def buildTree(rows, scoreF=entropy):
    if len(rows) == 0:
        return DecisionNode()
    currentScore = scoreF(rows)

    # Set up some variables to track the best criteria
    bestGain = 0.0
    bestCriteria = None
    bestSets = None

    cols = len(rows[0]) - 1
    for col in range(0, cols):
        # Generate the list of different values in this column
        colValues = {}
        for row in rows:
            colValues[row[col]] = 1

        # Now try dividing the rows up for each value in this column
        for value in colValues:
            set1, set2 = divideSet(rows, col, value)

            # Infomation gain
            p = float(len(set1)) / len(rows)
            gain = currentScore - p * scoreF(set1) - (1 - p) * scoreF(set2)

            if gain > bestGain:
                bestGain = gain
                bestCriteria = (col, value)
                bestSets = (set1, set2)

    # Create the subbranches
    if bestGain > 0:
        trueBranch = buildTree(bestSets[0], scoreF)
        falseBranch = buildTree(bestSets[1], scoreF)
        return DecisionNode(col=bestCriteria[0], value=bestCriteria[1],
                            tB=trueBranch, fB=falseBranch)
    else:
        return DecisionNode(results=uniqueCounts(rows))


def printTree(tree, indent=''):
    # Is this a leaf node?
    if tree.results is not None:
        print str(tree.results)
    else:
        # Print the criteria
        print str(tree.col) + ':' + str(tree.value) + '?'

        # Print the branches
        print indent + 'T->',
        printTree(tree.tB, indent + '  ')
        print indent + 'F->',
        printTree(tree.fB, indent + '  ')


def getWidth(tree):
    if tree.tB is None and tree.fB is None:
        return 1
    else:
        return getWidth(tree.tB) + getWidth(tree.fB)


def getDepth(tree):
    if tree.tB is None and tree.fB is None:
        return 0
    else:
        return max(getDepth(tree.tB), getWidth(tree.fB)) + 1


def drawTree(tree, jpeg='tree.jpg'):
    w = getWidth(tree) * 100
    h = getDepth(tree) * 100 + 120

    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    drawNode(draw, tree, w / 2, 20)
    img.save(jpeg, 'JPEG')


def drawNode(draw, tree, x, y):
    if tree.results is None:
        # Get thw width of each branch
        w1 = getWidth(tree.fB) * 100
        w2 = getWidth(tree.tB) * 100

        # Determine the total space required by this node
        left = x - (w1 + w2) / 2
        right = x + (w1 + w2) / 2

        # Draw the condition string
        draw.text((x - 20, y - 10), str(tree.col) + ':' + str(tree.value), (0, 0, 0))

        # Draw links to the branch
        draw.line((x, y, left + w1 / 2, y + 100), fill=(255, 0, 0))
        draw.line((x, y, right - w2 / 2, y + 100), fill=(255, 0, 0))

        # Draw the branch nodes
        drawNode(draw, tree.fB, left + w1 / 2, y + 100)
        drawNode(draw, tree.tB, right - w2 / 2, y + 100)
    else:
        txt = ' \n'.join(['%s:%d' % v for v in tree.results.items()])
        draw.text((x - 20, y), txt, (0, 0, 0))


def classify(observation, tree):
    if tree.results is not None:
        return tree.results
    else:
        v = observation[tree.col]

        if isinstance(v, int) or isinstance(v, float):
            if v >= tree.value:
                branch = tree.tB
            else:
                branch = tree.fB
        else:
            if v == tree.value:
                branch = tree.tB
            else:
                branch = tree.fB

        return classify(observation, branch)


def prune(tree, minGain):
    # If the branches aren't leaves, then prune them
    if tree.tB.results is None:
        prune(tree.tB, minGain)
    if tree.fB.results is None:
        prune(tree.fB, minGain)

    # If both the subbranches are now leaves, see if they should merged
    if tree.tB.results is not None and tree.fB.results is not None:
        # Build a combined dataset
        tB, fB = [], []

        for result, count in tree.tB.results.items():
            tB += [[result]] * count
        for result, count in tree.fB.results.items():
            fB += [[result]] * count

        # Test the reduction in entropy
        p1 = float(len(tB)) / len(tB + fB)
        p2 = float(len(fB)) / len(tB + fB)
        delta = entropy(tB + fB) - (entropy(tB) * p1 + entropy(fB) * p2)

        if delta < minGain:
            # Merge the branches
            tree.tB, tree.fB = None, None
            tree.results = uniqueCounts(tB + fB)


def mdClassify(observation, tree):
    if tree.results is not None:
        return tree.results
    else:
        value = observation[tree.col]

        if value is None:
            tR, fR = mdClassify(observation, tree.tB), mdClassify(observation, tree.fB)
            tCount = sum(tR.values())
            fCount = sum(fR.values())
            tW = float(tCount) / (tCount + fCount)
            fW = float(fCount) / (tCount + fCount)

            results = {}
            for result, count in tR.items():
                results.setdefault(result, 0)
                results[result] += tW * count
            for result, count in fR.items():
                results.setdefault(result, 0)
                results[result] += fW * count

            return results
        else:
            if isinstance(value, int) or isinstance(value, float):
                if value >= tree.value:
                    branch = tree.tB
                else:
                    branch = tree.fB
            else:
                if value == tree.value:
                    branch = tree.tB
                else:
                    branch = tree.fB

            return mdClassify(observation, branch)


def variance(rows):
    if len(rows) == 0:
        return 0.0

    data = [float(row[len(row) - 1]) for row in rows]

    mean = sum(data) / len(data)
    variance = sum([(d - mean) ** 2 for d in data]) / len(data)
    return variance


def testTreePredict():
    print divideSet(userData, 2, 'yes')

    print giniImpurity(userData)
    print entropy(userData)

    set1, set2 = divideSet(userData, 2, 'yes')
    print entropy(set1)
    print giniImpurity(set1)

    print
    tree = buildTree(userData)
    printTree(tree)
    drawTree(tree, jpeg='userTree.jpg')

    print
    print classify(['(direct)', 'USA', 'yes', 5], tree)

    print
    prune(tree, 0.1)
    printTree(tree)

    print
    prune(tree, 1.0)
    printTree(tree)

    print
    print mdClassify(['google', None, 'yes', None], tree)
    print mdClassify(['google', 'France', None, None], tree)