__author__ = 'Artanis'


import optimization

s = [1, 4, 3, 2, 7, 3, 6, 3, 2, 4, 5, 3]
print optimization.scheduleCost(s)
optimization.printSchedule(s)

domain = [(0, 9)] * (len(optimization.people) * 2)

print
s = optimization.randomOptimize(domain, optimization.scheduleCost)
print optimization.scheduleCost(s)
optimization.printSchedule(s)

print
s = optimization.hillClimb(domain, optimization.scheduleCost)
print optimization.scheduleCost(s)
optimization.printSchedule(s)

print
s = optimization.annealingOptimize(domain, optimization.scheduleCost)
print optimization.scheduleCost(s)
optimization.printSchedule(s)

print
s = optimization.geneticOptimize(domain, optimization.scheduleCost)
print optimization.scheduleCost(s)
optimization.printSchedule(s)
