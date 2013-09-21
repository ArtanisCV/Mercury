import urllib2
import xml.dom.minidom

__author__ = 'Artanis'

apiKey = "479NUNJHETN"


def getRandomRating(c):
    # Construct URL for getRandomProfile
    url = "http://services.hotornot.com/rest/?app_key=%s" % apiKey
    url += "&method=Rate.getRandomProfile&retrieve_num=%d" % c
    url += "&get_rate_info=true&meet_users_only=true"

    try:
        doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())
    except:
        return []

    emIds = doc.getElementsByTagName('emid')
    ratings = doc.getElementsByTagName('rating')

    # Combine the emids and ratings together into a list
    result = []

    for emId, rating in zip(emIds, ratings):
        if rating.firstChild is not None:
            result.append((emId.firstChild.data, rating.firstChild.data))

    return result


stateRegions = {'New England': ['ct', 'mn', 'ma', 'nh', 'ri', 'vt'],
                'Mid Atlantic': ['de', 'md', 'nj', 'ny', 'pa'],
                'South': ['al', 'ak', 'fl', 'ga', 'ky', 'la', 'ms', 'mo', 'nc', 'sc', 'tn', 'va', 'wv'],
                'Midwest': ['il', 'in', 'ia', 'ks', 'mi', 'ne', 'nd', 'oh', 'sd', 'wi'],
                'West': ['ak', 'ca', 'co', 'hi', 'id', 'mt', 'nv', 'or', 'ut', 'wa', 'wy']}


def getPeopleData(ratings):
    result = []

    for emId, rating in ratings:
        # URL for the MeetMe.getProfile method
        url = "http://services.hotornot.com/rest/?app_key=%s" % apiKey
        url += "&method=MeetMe.getProfile&emid=%s&get_keywords=true" % emId

        # Get all the info about this person
        try:
            rating = int(float(rating) + 0.5)

            doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())
            gender = doc.getElementsByTagName('gender')[0].firstChild.data
            age = doc.getElementsByTagName('age')[0].firstChild.data
            loc = doc.getElementsByTagName('location')[0].firstChild.data[0:2]

            # Convert state to region
            for r, s in stateRegions:
                if loc in s:
                    region = r

            if region is not None:
                result.append((gender, int(age), region, rating))
        except:
            pass

    return result


def testHotOrNot():
    data = getRandomRating(500)
    print len(data)

    pData = getPeopleData(data)
    print len(pData)

    import treePredict

    hotTree = treePredict.buildTree(pData, scoreF=treePredict.variance)
    treePredict.prune(hotTree, 0.5)
    treePredict.drawTree(hotTree, 'hotTree.jpg')

    south = treePredict.mdClassify((None, None, 'South'), hotTree)
    midAt = treePredict.mdClassify((None, None, 'Mid Atlantic'), hotTree)
    print south[10] / sum(south.values())
    print midAt[10] / sum(midAt.values())