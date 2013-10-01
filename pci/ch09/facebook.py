from xml.dom.minidom import parseString
from svm import *
from svmutil import *
import urllib
import md5
import webbrowser
import time


__author__ = 'Artanis'

apiKey = "Your API Key"
secret = "Your Secret Key"
facebookURL = "https://api.facebook.com/restserver.php"


def getSingleValue(node, tag):
    nl = node.getElementsByTagName(tag)

    if len(nl) > 0:
        tagNode = nl[0]

        if tagNode.hasChildNodes():
            return tagNode.firstChild.nodeValue

    return ''


def callId():
    return str(int(time.time() * 10))


class FbSession:
    def __init__(self):
        self.sessionSecret = None
        self.sessionKey = None
        self.token = self.createToken()
        webbrowser.open(self.getLogin())
        print "Press enter after logging in:", raw_input()
        self.getSession()

    def sendRequest(self, args):
        args['api_key'] = apiKey
        args['sig'] = self.makeHash(args)
        postData = urllib.urlencode(args)
        url = facebookURL + "?" + postData
        data = urllib.urlopen(url).read()
        return parseString(data)

    def makeHash(self, args):
        hasher = md5.new(''.join([x + '=' + args[x] for x in sorted(args.keys())]))
        if self.sessionSecret:
            hasher.update(self.sessionSecret)
        else:
            hasher.update(secret)
        return hasher.hexdigest()

    def createToken(self):
        res = self.sendRequest({'method': "facebook.auth.createToken"})
        return getSingleValue(res, 'token')

    def getLogin(self):
        return "http://api.facebook.com/login.php?api_key=" + apiKey + \
               "&auth_token=" + self.token

    def getSession(self):
        doc = self.sendRequest({'method': 'facebook.auth.getSession',
                                'auth_token': self.token})
        self.sessionKey = getSingleValue(doc, 'session_key')
        self.sessionSecret = getSingleValue(doc, 'secret')

    def getFriends(self):
        doc = self.sendRequest({'method': 'facebook.friends.get',
                                'session_key': self.sessionKey, 'call_id': callId()})
        results = []
        for node in doc.getElementsByTagName('result_elt'):
            results.append(node.firstChild.nodeValue)
        return results

    def getInfo(self, users):
        ulist = ','.join(users)
        fields = 'gender,current_location,relationship_status,' + \
                 'affiliations,hometown_location'

        doc = self.sendRequest({'method': 'facebook.users.getInfo',
                                'session_key': self.sessionKey, 'call_id': callId(),
                                'users': ulist, 'fields': fields})

        results = {}
        for node, uid in zip(doc.getElementsByTagName('result_elt'), users):
            # Get the location
            locNode = node.getElementsByTagName('hometown_location')[0]
            loc = getSingleValue(locNode, 'city') + ', ' + getSingleValue(locNode, 'state')

            # Get school
            college = ''
            gradYear = '0'
            affiliations = node.getElementsByTagName('affiliations_elt')
            for aff in affiliations:
                # Type 1 is college
                if getSingleValue(aff, 'type') == '1':
                    college = getSingleValue(aff, 'name')
                    gradYear = getSingleValue(aff, 'year')

            results[uid] = {'gender': getSingleValue(node, 'gender'),
                            'status': getSingleValue(node, 'relationship_status'),
                            'location': loc, 'college': college, 'year': gradYear}
        return results

    def areFriends(self, idList1, idList2):
        id1 = ','.join(idList1)
        id2 = ','.join(idList2)

        doc = self.sendRequest({'method': 'facebook.friends.areFriends',
                                'session_key': self.sessionKey, 'call_id': callId(),
                                'id1': id1, 'id2': id2})

        results = []
        for node in doc.getElementsByTagName('result_elt'):
            results.append(node.firstChild.nodeValue)
        return results

    def makeDataset(self):
        # Get all the info for all my friends
        friends = self.getFriends()
        infos = self.getInfo(friends)
        ids1, ids2 = [], []
        rows = []

        # Nested loop to look at every pair of friends
        for i in range(len(friends)):
            f1 = friends[i]
            data1 = infos[f1]

            # Start at i+1 so we don't double up
            for j in range(i + 1, len(friends)):
                f2 = friends[j]
                data2 = infos[f2]

                ids1.append(f1)
                ids2.append(f2)

                # Generate some numbers from the data
                if data1['college'] == data2['college']:
                    sameSchool = 1
                else:
                    sameSchool = 0
                isMale1 = (data1['gender'] == 'Male') and 1 or 0
                isMale2 = (data2['gender'] == 'Male') and 1 or 0
                row = [isMale1, int(data1['year']), isMale2, int(data2['year']), sameSchool]
                rows.append(row)

        # Call areFriends in blocks for every pair of people
        areFriends = []
        for i in range(0, len(ids1), 30):
            j = min(i + 30, len(ids1))
            pa = self.areFriends(ids1[i: j], ids2[i: j])
            areFriends += pa

        return areFriends, rows


def testFacebook():
    session = FbSession()

    friends = session.getFriends()
    print friends[1]
    print session.getInfo(friends[0:2])

    answers, data = session.makeDataset()
    problem = svm_problem(answers, data)
    param = svm_parameter('-t 2')
    model = svm_train(problem, param)
    print svm_predict([1], [[1, 2003, 1, 2003, 1]], model)[0]  # Two men, same year, same school
    print svm_predict([0], [[1, 2003, 1, 1996, 0]], model)[0]  # Different years, different schools