from random import random, randint, choice
from copy import deepcopy
from math import log

__author__ = 'Artanis'


class FWrapper:
    def __init__(self, function, childCount, name):
        self.function = function
        self.childCount = childCount
        self.name = name


class Node:
    def __init__(self, fWrapper, children):
        self.function = fWrapper.function
        self.name = fWrapper.name
        self.children = children

    def evaluate(self, inputs):
        results = [child.evaluate(inputs) for child in self.children]
        return self.function(results)

    def display(self, indent=0):
        print (' ' * indent) + self.name

        for child in self.children:
            child.display(indent + 1)


class ParamNode:
    def __init__(self, idx):
        self.idx = idx

    def evaluate(self, inputs):
        return inputs[self.idx]

    def display(self, indent=0):
        print '%sp%d' % (' ' * indent, self.idx)


class ConstNode:
    def __init__(self, value):
        self.value = value

    def evaluate(self, inputs):
        return self.value

    def display(self, indent=0):
        print '%s%d' % (' ' * indent, self.value)


addW = FWrapper(lambda l: l[0] + l[1], 2, 'add')
subW = FWrapper(lambda l: l[0] - l[1], 2, 'subtract')
mulW = FWrapper(lambda l: l[0] * l[1], 2, 'multiply')


def ifFunc(l):
    if l[0] > 0:
        return l[1]
    else:
        return l[2]

ifW = FWrapper(ifFunc, 3, 'if')


def isGreater(l):
    if l[0] > l[1]:
        return 1
    else:
        return 0

gtW = FWrapper(isGreater, 2, 'isGreater')

fList = [addW, subW, mulW, ifW, gtW]


def exampleTree():
    return Node(
        ifW,
        [
            Node(gtW, [ParamNode(0), ConstNode(3)]),
            Node(addW, [ParamNode(1), ConstNode(5)]),
            Node(subW, [ParamNode(1), ConstNode(2)])
        ]
    )


def makeRandomTree(nParam, maxDepth=4, fProb=0.5, pProb=0.6):
    if random() < fProb and maxDepth > 0:
        fW = choice(fList)
        children = [makeRandomTree(nParam, maxDepth - 1, fProb, pProb)
                    for i in range(fW.childCount)]
        return Node(fW, children)
    elif random() < pProb:
        return ParamNode(randint(0, nParam - 1))
    else:
        return ConstNode(randint(0, 10))


def hiddenFunction(x, y):
    return x**2 + 2 * y + 3 * x + 5


def buildHiddenSet():
    rows = []

    for i in range(200):
        x = randint(0, 40)
        y = randint(0, 40)
        rows.append([x, y, hiddenFunction(x, y)])

    return rows


def scoreFunction(tree, data):
    dif = 0

    for row in data:
        value = tree.evaluate([row[0], row[1]])
        dif += abs(value - row[2])

    return dif


def mutate(tree, nParam, changeProb=0.1):
    if random() < changeProb:
        return makeRandomTree(nParam)
    else:
        result = deepcopy(tree)

        if hasattr(tree, 'children'):
            result.children = [mutate(child, nParam, changeProb)
                               for child in tree.children]

        return result


def crossOver(tree1, tree2, swapProb=0.7, top=True):
    if random() < swapProb and not top:
        return deepcopy(tree2)
    else:
        result = deepcopy(tree1)

        if hasattr(tree1, 'children') and hasattr(tree2, 'children'):
            result.children = [crossOver(child, choice(tree2.children), swapProb, False)
                               for child in tree1.children]

        return result


def evolve(nParam, popSize, rankFunc, maxGen=500,
           mutateProb=0.1, crossProb=0.4, expThred=0.7, newProb=0.05):
    # Returns a random number, tending towards lower numbers. The lower
    # expThred is, more lower numbers you will get
    def selectIndex(maximum):
        return int(log(random()) / log(expThred)) % maximum

    # Create a random initial population
    population = [makeRandomTree(nParam) for i in range(popSize)]

    for i in range(maxGen + 1):
        scores = rankFunc(population)

        print scores[0][0]
        if scores[0][0] == 0:
            break

        if i == maxGen:
            break

        # The two best always make it
        newPop = [scores[0][1], scores[1][1]]

        # Build the next generation
        while len(newPop) < popSize:
            if random() > newProb:
                newPop.append(
                    mutate(
                        crossOver(scores[selectIndex(len(scores))][1],
                                  scores[selectIndex(len(scores))][1],
                                  swapProb=crossProb),
                        nParam,
                        changeProb=mutateProb
                    )
                )
            else:
                # Add a rondom node to mix things up
                newPop.append(makeRandomTree(nParam))

        population = newPop

    scores[0][1].display()
    return scores[0][1]


def getRankFunction(dataset):
    def rankFunction(population):
        scores = [(scoreFunction(tree, dataset), tree) for tree in population]
        scores.sort()
        return scores
    return rankFunction


def gridGame(trees, board):
    # Remember the last move for each player
    lastMove = [-1, -1]

    # Remember the player's locations
    locations = [[randint(0, board[0]), randint(0, board[1])]]

    # Put the second player a sufficient distance from the first
    locations.append([(locations[0][0] + 2) % (board[0] + 1),
                     (locations[0][1] + 2) % (board[1] + 1)])

    # Maximum of 50 moves before a tie
    for m in range(50):
        # For each player
        for i in range(2):
            loc = locations[i][:] + locations[1 - i][:]
            loc.append(lastMove[i])
            move = trees[i].evaluate(loc) % 4

            # You lose if you move the same direction twice in a row
            if lastMove[i] == move:
                return 1 - i
            lastMove[i] = move

            if move == 0:
                locations[i][0] -= 1
                if locations[i][0] < 0:
                    locations[i][0] = 0
            elif move == 1:
                locations[i][0] += 1
                if locations[i][0] > board[0]:
                    locations[i][0] = board[0]
            elif move == 2:
                locations[i][1] -= 1
                if locations[i][1] < 0:
                    locations[i][1] = 0
            else:
                locations[i][1] += 1
                if locations[i][1] > board[1]:
                    locations[i][1] = board[1]

            # If you have captured the other player, you win
            if locations[i] == locations[i - 1]:
                return i

    return -1


def tournament(players, board):
    # Count losses
    losses = [0 for player in players]

    # Every player plays every other player
    for i in range(len(players)):
        for j in range(len(players)):
            if i == j:
                continue

            # Who is the winner?
            winner = gridGame([players[i], players[j]], board)

            # Two points for a loss, one point for a tie
            if winner == 0:
                losses[j] += 2
            elif winner == 1:
                losses[i] += 2
            elif winner == -1:
                losses[i] += 1
                losses[j] += 1

    # Sort and return the results
    results = zip(losses, players)
    results.sort()
    return results


class HumanPlayer:
    def __init__(self, board):
        self.board = board

    def evaluate(self, locations):
        # Get my location and the location of other players
        me = tuple(locations[0: 2])
        others = [tuple(locations[x: x + 2]) for x in range(2, len(locations) - 1, 2)]

        # Display the board
        for i in range(self.board[0]):
            for j in range(self.board[1]):
                if (i, j) == me:
                    print '0',
                elif (i, j) in others:
                    print 'X',
                else:
                    print '.',

            print

        # Show moves, for reference
        print 'Your last move was %d' % locations[len(locations) - 1]
        print ' 0'
        print '2 3'
        print ' 1'
        print 'Enter move: ',

        # Return whatever the user enters
        move = int(raw_input())
        return move


def testGP():
    egTree = exampleTree()
    print egTree.evaluate([2, 3])
    print egTree.evaluate([5, 3])

    print
    egTree.display()

    print
    random1 = makeRandomTree(2)
    print random1.evaluate([7, 1])
    print random1.evaluate([2, 4])

    random2 = makeRandomTree(2)
    print random2.evaluate([5, 3])
    print random2.evaluate([5, 20])

    print
    random1.display()

    print
    random2.display()

    print
    hiddenSet = buildHiddenSet()
    print scoreFunction(random2, hiddenSet)
    print scoreFunction(random1, hiddenSet)

    print
    random2 = makeRandomTree(2)
    random2.display()

    mutTree = mutate(random2, 2)
    mutTree.display()

    print
    print scoreFunction(random2, hiddenSet)
    print scoreFunction(mutTree, hiddenSet)

    print
    random1 = makeRandomTree(1)
    random1.display()

    random2 = makeRandomTree(2)
    random2.display()

    cross = crossOver(random1, random2)
    cross.display()

    #print
    #rankFunction = getRankFunction(buildHiddenSet())
    #evolve(2, 500, rankFunction, mutateProb=0.2, crossProb=0.1, expThred=0.7, newProb=0.1)

    print
    board = (3, 3)
    p1 = makeRandomTree(5)
    p2 = makeRandomTree(5)
    print gridGame([p1, p2], board)
    winner = evolve(5, 100, lambda players: tournament(players, board), maxGen=50)
    gridGame([winner, HumanPlayer(board)], board)