import time
import urllib2
import xml.dom.minidom


kayakKey = 'YOUR KEY HERE'


def getKayakSession():
    # Construct the URL to start a session
    url = 'http://www.kayak.com/k/ident/apisession?token=%s&version=1' % kayakKey

    # Parse the resulting XML
    doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())

    # Find <sid>xxxxxxxx</sid>
    sessionId = doc.getElementsByTagName('sid')[0].firstChild.data
    return sessionId


def flightSearch(sessionId, origin, destination, depart_date):
    # Construct search URL
    url = 'http://www.kayak.com/s/apisearch?basicmode=true&oneway=y&origin=%s' % origin
    url += '&destination=%s&depart_date=%s' % (destination, depart_date)
    url += '&return_date=none&depart_time=a&return_time=a'
    url += '&travelers=1&cabin=e&action=doFlights&apimode=1'
    url += '&_sid_=%s&version=1' % sessionId

    # Get the XML
    doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())

    # Extract the search ID
    searchId = doc.getElementsByTagName('searchid')[0].firstChild.data

    return searchId


def flightSearchResults(sessionId, searchId):
    def parsePrice(p):
        return float(p[1:].replace(',', ''))

    # Polling loop
    while 1:
        time.sleep(2)

        # Construct URL for polling
        url = 'http://www.kayak.com/s/basic/flight?'
        url += 'searchid=%s&c=5&apimode=1&_sid_=%s&version=1' % (searchId, sessionId)
        doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())

        # Look for morepending tag, and wait until it is no longer true
        morePending = doc.getElementsByTagName('morepending')[0].firstChild
        if morePending is None or morePending.data == 'false':
            break

    # Now download the complete list
    url = 'http://www.kayak.com/s/basic/flight?'
    url += 'searchid=%s&c=999&apimode=1&_sid_=%s&version=1' % (searchId, sessionId)
    doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())

    # Get the various elements as lists
    prices = doc.getElementsByTagName('price')
    departures = doc.getElementsByTagName('depart')
    arrivals = doc.getElementsByTagName('arrive')

    # Zip them together
    return zip([p.firstChild.data.split(' ')[1] for p in departures],
               [p.firstChild.data.split(' ')[1] for p in arrivals],
               [parsePrice(p.firstChild.data) for p in prices])


def createSchedule(people, dest, dep, ret):
    # Get a session id for these searches
    sessionId = getKayakSession()
    flights = {}

    for p in people:
        name, origin = p
        # Outbound flight
        searchId = flightSearch(sessionId, origin, dest, dep)
        flights[(origin, dest)] = flightSearchResults(sessionId, searchId)

        # Return flight
        searchId = flightSearch(sessionId, dest, origin, ret)
        flights[(dest, origin)] = flightSearchResults(sessionId, searchId)

    return flights


def testKayak():
    dom = xml.dom.minidom.parseString('<data><rec>Hello!</rec></data>')
    print dom

    rec = dom.getElementsByTagName('rec')
    print rec
    print rec[0].firstChild
    print rec[0].firstChild.data

    # sessionId = getKayakSession()
    # searchId = flightSearch(sessionId, 'BOS', 'LGA', '11/17/2006')
    # print flightSearchResults(sessionId, searchId)[0: 3]
    #
    # import flight
    # import optimization
    #
    # flights = createSchedule(flight.people[0: 2], 'LGA', '11/17/2006', '11/19/2006')
    # flight.flights = flights
    # domain = [(0, 30)] * len(flights)
    #
    # s = optimization.geneticOptimize(domain, flight.scheduleCost)
    # flight.printSchedule(s)