import xml.dom.minidom
import urllib2

__author__ = 'Artanis'

zwsKey = "X1-ZWz1chwxis15aj_9skq6"


def getAddressData(address, city):
    escAddress = address.replace(' ', '+')

    # Construct the URL
    url = 'http://www.zillow.com/webservice/GetDeepSearchResults.htm?'
    url += 'zws-id=%s&address=%s&citystatezip=%s' % (zwsKey, escAddress, city)

    # Parse resulting XML
    try:
        doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())
        code = doc.getElementsByTagName('code')[0].firstChild.data

        # code 0 means success; otherwise, there was an error
        if code != '0':
            return None
    except:
        return None

    # Extract the info about this property
    try:
        zipCode = doc.getElementsByTagName('zipcode')[0].firstChild.data
        useCode = doc.getElementsByTagName('useCode')[0].firstChild.data
        year = doc.getElementsByTagName('yearBuilt')[0].firstChild.data
        bathrooms = doc.getElementsByTagName('bathrooms')[0].firstChild.data
        bedrooms = doc.getElementsByTagName('bedrooms')[0].firstChild.data
        # rooms = doc.getElementsByTagName('totalRooms')[0].firstChild.data
        price = doc.getElementsByTagName('amount')[0].firstChild.data
    except:
        return None

    return zipCode, useCode, int(year), float(bathrooms), int(bedrooms), price


def getPriceList():
    priceList = []

    for line in file('addressList.txt'):
        data = getAddressData(line.strip(), 'Cambridge,MA')
        if data is not None:
            priceList.append(data)

    return priceList


def testZillow():
    import treePredict

    houseData = getPriceList()
    houseTree = treePredict.buildTree(houseData, scoreF=treePredict.variance)
    treePredict.drawTree(houseTree, 'houseTree.jpg')