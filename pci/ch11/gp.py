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


def testGP():
    egTree = exampleTree()
    print egTree.evaluate([2, 3])
    print egTree.evaluate([5, 3])

    print
    egTree.display()
