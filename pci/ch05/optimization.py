import time
import random
import math

__author__ = 'Artanis'

people = [('Seymour', 'BOS'),
          ('Franny', 'DAL'),
          ('Zooey', 'CAK'),
          ('Walt', 'MIA'),
          ('Buddy', 'ORD'),
          ('Les', 'OMA')]

# LaGuardia airport in New York
destination = 'LGA'

flights = {}

for line in file('schedule.txt'):
    origin, dest, depart, arrive, price = line.strip().split(',')
    flights.setdefault((origin, dest), [])

    # Add details to the list of possible flights
    flights[(origin, dest)].append((depart, arrive, int(price)))


def getMinutes(t):
    x = time.strptime(t, '%H:%M')
    return x[3] * 60 + x[4]


def printSchedule(v):
    for idx in range(len(v) / 2):
        name = people[idx][0]
        origin = people[idx][1]
        out = flights[(origin, destination)][int(v[idx * 2])]
        ret = flights[(destination, origin)][int(v[idx * 2 + 1])]
        print '%10s%10s %5s-%5s $%3s %5s-%5s $%3s' % (name, origin,
                                                      out[0], out[1], out[2],
                                                      ret[0], ret[1], ret[2])


def scheduleCost(v):
    totalPrice = 0
    lastestArrival = 0
    earliestDep = 24 * 60

    for idx in range(len(v) / 2):
        # Get the inbound and outbound flights
        origin = people[idx][1]
        out = flights[(origin, destination)][int(v[idx * 2])]
        ret = flights[(destination, origin)][int(v[idx * 2 + 1])]

        # Total price is the price of all outbound and return flights
        totalPrice += out[2] + ret[2]

        # Track the latest arrival and earliest departure
        if lastestArrival < getMinutes(out[1]):
            lastestArrival = getMinutes(out[1])

        if earliestDep > getMinutes(ret[0]):
            earliestDep = getMinutes(ret[0])

    # Every person must wait at the airport until the latest person arrives.
    # They also must arrive at the same time and wait for their flights.
    totalWait = 0

    for idx in range(len(v) / 2):
        origin = people[idx][1]
        out = flights[(origin, destination)][int(v[idx * 2])]
        ret = flights[(destination, origin)][int(v[idx * 2 + 1])]

        totalWait += lastestArrival - getMinutes(out[1])
        totalWait += getMinutes(ret[0]) - earliestDep

    # Does this solution require an extra day of car rental? That'll be $50!
    if lastestArrival < earliestDep:
        totalPrice += 50

    return totalPrice + totalWait


def randomOptimize(domain, costF):
    best = 999999999
    bestR = None

    for i in range(1000):
        # Create a random solution
        r = [random.randint(domain[i][0], domain[i][1])
             for i in range(len(domain))]

        # Get the cost
        cost = costF(r)

        # Compare it to the best one so far
        if cost < best:
            best = cost
            bestR = r

    return bestR


def hillClimb(domain, costF):
    # Create a random solution
    r = [random.randint(domain[i][0], domain[i][1])
         for i in range(len(domain))]

    # Main loop
    while 1:
        # Create list of neighboring solutions
        neighbors = []

        for j in range(len(domain)):
            # One away in each direction
            if r[j] > domain[j][0]:
                neighbors.append(r[0: j] + [r[j] - 1] + r[j + 1:])
            if r[j] < domain[j][1]:
                neighbors.append(r[0: j] + [r[j] + 1] + r[j + 1:])

        # See what the best solution amongst the neighbors is
        current = costF(r)
        best = current

        for j in range(len(neighbors)):
            cost = costF(neighbors[j])

            if cost < best:
                best = cost
                r = neighbors[j]

        # If there's no improvement, then we've reached the top
        if best == current:
            break

    return r


def annealingOptimize(domain, costF, T=10000.0, cool=0.95, step=1):
    # Initialize the values randomly
    r = [float(random.randint(domain[i][0], domain[i][1]))
         for i in range(len(domain))]

    while T > 0.1:
        # Choose one of the indices
        i = random.randint(0, len(domain) - 1)

        # Choose a direction to change it
        dir = random.randint(-step, step)

        # Create a new list with one of the values changed
        rb = r[:]
        rb[i] += dir

        if rb[i] < domain[i][0]:
            rb[i] = domain[i][0]
        elif rb[i] > domain[i][1]:
            rb[i] = domain[i][1]

        # Calculate the current cost and the new cost
        ea = costF(r)
        eb = costF(rb)

        # Is it better, or does it make the probability cutoff?
        if eb < ea or random.random() < pow(math.e, -(eb - ea) / T):
            r = rb

        # Decrease the temperature
        T = T * cool

    return r


def geneticOptimize(domain, costF, popSize=50, step=1, mutProb=0.2, elite=0.2, maxIter=100):
    # Mutation Operation
    def mutate(v):
        i = random.randint(0, len(domain) - 1)

        if random.random() < 0.5 and v[i] > domain[i][0]:
            return v[0: i] + [v[i] - step] + v[i + 1:]
        elif v[i] < domain[i][1]:
            return v[0: i] + [v[i] + step] + v[i + 1:]
        else:
            return v

    # Crossover Operation
    def crossover(v1, v2):
        i = random.randint(1, len(domain) - 2)
        return v1[0: i] + v2[i:]

    # Build the initial population
    pop = []
    for i in range(popSize):
        v = [random.randint(domain[i][0], domain[i][1])
             for i in range(len(domain))]
        pop.append(v)

    # How many winners from each generation?
    topElite = int(elite * popSize)

    # Main loop
    for i in range(maxIter):
        scores = [(costF(v), v) for v in pop]
        scores.sort()
        ranked = [v for (s, v) in scores]

        # Start with the pure winners
        pop = ranked[0 : topElite]

        # Add mutated and bred forms of the winners
        while len(pop) < popSize:
            if random.random() < mutProb:
                # Mutation
                c = random.randint(0, topElite)
                pop.append(mutate(ranked[c]))
            else:
                # Crossover
                c1 = random.randint(0, topElite)
                c2 = random.randint(0, topElite)
                pop.append(crossover(ranked[c1], ranked[c2]))

        # Print current best score
        print scores[0][0]

    return scores[0][1]