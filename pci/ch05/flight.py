import time

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


def testFlight():
    for line in file('schedule.txt'):
        origin, dest, depart, arrive, price = line.strip().split(',')
        flights.setdefault((origin, dest), [])

        # Add details to the list of possible flights
        flights[(origin, dest)].append((depart, arrive, int(price)))

    s = [1, 4, 3, 2, 7, 3, 6, 3, 2, 4, 5, 3]
    print scheduleCost(s)
    printSchedule(s)

    domain = [(0, 9)] * (len(people) * 2)

    import optimization

    print
    s = optimization.randomOptimize(domain, scheduleCost)
    print scheduleCost(s)
    printSchedule(s)

    print
    s = optimization.hillClimb(domain, scheduleCost)
    print scheduleCost(s)
    printSchedule(s)

    print
    s = optimization.annealingOptimize(domain, scheduleCost)
    print scheduleCost(s)
    printSchedule(s)

    print
    s = optimization.geneticOptimize(domain, scheduleCost)
    print scheduleCost(s)
    printSchedule(s)