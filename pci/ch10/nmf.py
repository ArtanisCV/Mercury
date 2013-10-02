from numpy import *
import random

__author__ = 'Artanis'


def difCost(m1, m2):
    a1 = m1.A
    a2 = m2.A

    return sum(pow(a1 - a2, 2))


def factorize(v, r=10, maxIter=50):
    n, m = v.shape
    eps = 1e-10

    # Initialize the weight and feature matrics with random values
    w = matrix([[random.random() for j in range(r)] for i in range(n)])
    h = matrix([[random.random() for j in range(m)] for i in range(r)])

    # Perform operation a maximum of iter times
    for i in range(maxIter):
        v_hat = w * h

        # Calculate the current difference
        cost = difCost(v, v_hat)

        if i % 10 == 0:
            print cost

        # Terminate if the matrix has been fully factorized
        if cost == 0:
            break

        # Update the feature matrix
        wv = w.transpose() * v
        wwh = w.transpose() * w * h + eps
        h = matrix(h.A * wv.A / wwh.A)  # element-wise operations

        # Update weights matrix
        vh = v * h.transpose()
        whh = w * h * h.transpose() + eps
        w = matrix(w.A * vh.A / whh.A)  # element-wise operations

    return w, h


def testNMF():
    l = [[1, 2, 3], [4, 5, 6]]
    print l

    m1 = matrix(l)
    print m1

    m2 = matrix([[1, 2], [3, 4], [5, 6]])
    print m2
    print m1 * m2

    print m1.shape
    print m2.shape

    a1 = m1.A
    print a1

    a2 = array([[1, 2, 3], [1, 2, 3]])
    print a1 * a2

    print
    w, h = factorize(m1 * m2, 3, 100)
    print w
    print h
    print w * h
    print m1 * m2