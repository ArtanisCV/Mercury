from xml.dom.minidom import parse, parseString, Node
import httplib

__author__ = 'Artanis'

devKey = '3de544aa-c632-4a13-82bf-4dbd0923431d'
appKey = 'ArtanisP-4ad6-4f55-a580-05a5f7f33a33'
certKey = 'ce67a17d-f4f0-4f27-a6bb-ec4e68cd2f91'
userToken = 'AgAAAA**AQAAAA**aAAAAA**CopJUg**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wFk4GhC5CCog+\
             dj6x9nY+seQ**PFsCAA**AAMAAA**gbg3W9fpfOf7BI/iTCqKJu5YHZDp16yepuA6RDd0c5ULlU\
             EjqJU/jG12Cm+cCQMBDrdjCK/hEY8ihy8iSUugGhGksHGwlncifmWpFumuHdmmX8ssQDC2obnC4\
             DVNLjnFNRTai7eJNyS7n/9I1Q3LNur+rT/cTYDml+pTme7jtIgVVRUv/fnljMkzlkpFVBL3RSMF\
             FFRlb4DFUp3rB4Ke8iB+b8zqhwZeTZNoK/QQabyaKPnc1X2Qg5SLqkHLbVs0ioEFGmBTQCueLhm\
             rdjotFAoKIgk0yjn6JU6UxYJ0C+nHXb1EE9rSyfbC5NG+hch5fXuh+101GZt3pefSKjTSWkbcus\
             EFRwKANsc9t/g0hSW0vMi77YV5RxkL/fZCq7AuPqaE1MfJE+2ve+egahxF1YUTqcYcRmwxtb9RW\
             tC8ANHyLmH/7qqzn47XM9F8Suvqewz2LAUkKGX5Am0+8Jw7jCAA9JHFeAyevZii7rDyDt/OHhKl\
             eLlEeM4A3txJ0+VDfmXCob3UaRruPfK12WP/XtoiErZBmmtHspUJelhXRr8k/mICrSXz+hWYqSd\
             BtmPmjGMGIx/1/FqR0vEPCNDexdcA0I05hb/VKmXJ3NoZHrly/JYgQFYoixZjaSvc1WC8bhKE/q\
             RDdSJveQWlGnzN4acNADYR4yRGEt7Ek3Sq7kQwPwyp7JtgaAUhxabn+as7rEb2SCEaSicLhzm+d\
             dxLp79IM2H2MIO+EVH0uECFuwUYRd4KH1bM7ArFm8PeY1fT'
serverUrl = 'api.ebay.com'


def getHeaders(apiCall, siteId="0", compatabilityLevel="433"):
    headers = {"X-EBAY-API-COMPATIBILITY-LEVEL": compatabilityLevel,
               "X-EBAY-API-DEV-NAME": devKey,
               "X-EBAY-API-APP-NAME": appKey,
               "X-EBAY-API-CERT-NAME": certKey,
               "X-EBAY-API-CALL-NAME": apiCall,
               "X-EBAY-API-SITEID": siteId,
               "Content-Type": "text/xml"}
    return headers


def sendRequest(apiCall, xmlParameters):
    connection = httplib.HTTPSConnection(serverUrl)
    connection.request("POST", '/ws/api.dll', xmlParameters, getHeaders(apiCall))
    response = connection.getresponse()

    if response.position != 200:
        print "Error sending request:" + response.reason
    else:
        data = response.read()
        connection.close()

    return data


def getSingleValue(node, tag):
    nl = node.getElementsByTagName(tag)

    if len(nl) > 0:
        tagNode = nl[0]

        if tagNode.hasChildNodes():
            return tagNode.firstChild.nodeValue

    return '-1'


def doSearch(query, categoryId=None, page=1):
    xml = "<?xml version='1.0' encoding='utf-8'?>" + \
          "<GetSearchResultsRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">" + \
          "<RequesterCredentials><eBayAuthToken>" + \
          userToken + \
          "</eBayAuthToken></RequesterCredentials>" + \
          "<Pagination>" + \
          "<EntriesPerPage>200</EntriesPerPage>" + \
          "<PageNumber>" + str(page) + "</PageNumber>" + \
          "</Pagination>" + \
          "<Query>" + query + "</Query>"
    if categoryId is not None:
        xml += "<CategoryID>" + str(categoryId) + "</CategoryID>"
    xml += "</GetSearchResultsRequest>"

    data = sendRequest('GetSearchResults', xml)
    response = parseString(data)
    itemNodes = response.getElementsByTagName('Item')
    results = []
    for item in itemNodes:
        itemId = getSingleValue(item, 'ItemID')
        itemTitle = getSingleValue(item, 'Title')
        itemPrice = getSingleValue(item, 'CurrentPrice')
        itemEnds = getSingleValue(item, 'EndTime')
        results.append((itemId, itemTitle, itemPrice, itemEnds))
    return results


def getCategory(query='', parentId=None, siteId='0'):
    query = query.lower()

    xml = "<?xml version='1.0' encoding='utf-8'?>" + \
          "<GetCategoriesRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">" + \
          "<RequesterCredentials><eBayAuthToken>" + \
          userToken + \
          "</eBayAuthToken></RequesterCredentials>" + \
          "<DetailLevel>ReturnAll</DetailLevel>" + \
          "<ViewAllNodes>true</ViewAllNodes>" + \
          "<CategorySiteID>" + siteId + "</CategorySiteID>"
    if parentId is None:
        xml += "<LevelLimit>1</LevelLimit>"
    else:
        xml += "<CategoryParent>" + str(parentId) + "</CategoryParent>"
        xml += "</GetCategoriesRequest>"

    data = sendRequest('GetCategories', xml)
    categoryList = parseString(data)
    catNodes = categoryList.getElementsByTagName('Category')
    for node in catNodes:
        catId = getSingleValue(node, 'CategoryID')
        name = getSingleValue(node, 'CategoryName')
        if name.lower().find(query) != -1:
            print catId, name


def getItem(itemId):
    xml = "<?xml version='1.0' encoding='utf-8'?>" + \
          "<GetItemRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">" + \
          "<RequesterCredentials><eBayAuthToken>" + \
          userToken + \
          "</eBayAuthToken></RequesterCredentials>" + \
          "<ItemID>" + str(itemId) + "</ItemID>" + \
          "<DetailLevel>ItemReturnAttributes</DetailLevel>" + \
          "</GetItemRequest>"

    data = sendRequest('GetItem', xml)
    result = {}
    response = parseString(data)

    result['title'] = getSingleValue(response, 'Title')

    sellingStatusNode = response.getElementsByTagName('SellingStatus')[0];
    result['price'] = getSingleValue(sellingStatusNode, 'CurrentPrice')
    result['bids'] = getSingleValue(sellingStatusNode, 'BidCount')

    seller = response.getElementsByTagName('Seller')
    result['feedback'] = getSingleValue(seller[0], 'FeedbackScore')

    attributeSet = response.getElementsByTagName('Attribute')
    attributes = {}
    for att in attributeSet:
        attId = att.attributes.getNamedItem('attributeID').nodeValue
        attValue = getSingleValue(att, 'ValueLiteral')
        attributes[attId] = attValue
    result['attributes'] = attributes

    return result


def makeLaptopDataset():
    searchResults = doSearch('laptop', categoryId=51148)
    result = []

    for r in searchResults:
        item = getItem(r[0])
        att = item['attributes']
        try:
            data = (float(att['12']), float(att['26444']),
                    float(att['26446']), float(att['25710']),
                    float(item['feedback']))
            entry = {'input': data, 'result': float(item['price'])}

            result.append(entry)
        except:
            print item['title'] + ' failed'

    return result


def testEbayPredict():
    laptops = doSearch('laptop')
    print laptops[0: 10]

    getCategory('computers')
    getCategory('laptops', parentId=58058)
    laptops = doSearch('laptop', categoryId=51148)
    print laptops[0: 10]

    print getItem(laptops[7][0])

    dataset = makeLaptopDataset()

    import numPredict

    print numPredict.knnEstimate(dataset, (512, 1000, 14, 40, 1000))
    print numPredict.knnEstimate(dataset, (1024, 1000, 14, 40, 1000))
    print numPredict.knnEstimate(dataset, (1024, 1000, 14, 60, 0))
    print numPredict.knnEstimate(dataset, (1024, 2000, 14, 60, 1000))