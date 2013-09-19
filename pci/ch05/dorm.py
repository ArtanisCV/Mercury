__author__ = 'Artanis'


# The dorms, each of which has two available spaces
dorms = ['Zeus', 'Athena', 'Hercules', 'Bacchus', 'Pluto']

# People, along with their first and second choices
prefs = [('Toby', ('Bacchus', 'Hercules')),
         ('Steve', ('Zeus', 'Pluto')),
         ('Andrea', ('Athena', 'Zeus')),
         ('Sarah', ('Zeus', 'Pluto')),
         ('Dave', ('Athena', 'Bacchus')),
         ('Jeff', ('Hercules', 'Pluto')),
         ('Fred', ('Pluto', 'Athena')),
         ('Suzie', ('Bacchus', 'Hercules')),
         ('Laura', ('Bacchus', 'Hercules')),
         ('Neil', ('Hercules', 'Athena'))]

# [(0, 9), (0, 8), (0, 7), (0, 6), ..., (0, 0)]
domain = [(0, (len(dorms) * 2) - i - 1)
          for i in range(0, len(dorms) * 2)]


def printSolution(v):
    slots = []

    # Create two slots for each dorm
    for i in range(len(dorms)):
        slots += [i, i]

    # Loop over each students assignment
    for i in range(len(v)):
        x = int(v[i])

        # Choose the slot from the remaining ones
        dorm = dorms[slots[x]]

        # Show the student and assigned dorm
        print prefs[i][0], dorm

        # Remove this slot
        del slots[x]


def dormCost(v):
    cost = 0

    # Create a list of slots
    slots = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]

    # Loop over each student
    for i in range(len(v)):
        x = int(v[i])
        dorm = dorms[slots[x]]
        pref = prefs[i][1]

        # First chioce costs 0, second choice costs 1, not on the list costs 3
        if pref[0] == dorm:
            cost += 0
        elif prefs[1] == dorm:
            cost += 1
        else:
            cost += 3

        # Remove selected slot
        del slots[x]

    return cost


def testDorm():
    printSolution([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    import optimization

    s = optimization.randomOptimize(domain, dormCost)
    print dormCost(s)

    print
    s = optimization.geneticOptimize(domain, dormCost)
    printSolution(s)