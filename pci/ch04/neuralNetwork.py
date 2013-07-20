from math import tanh
from pysqlite2 import dbapi2 as sqlite

__author__ = 'Artanis'


class searchNet:
    def __init__(self, dbName):
        self.conn = sqlite.connect(dbName)

    def __del__(self):
        self.conn.close()

    def createTables(self):
        self.conn.execute("drop table if exists HiddenNode")
        self.conn.execute("create table HiddenNode(createKey)")

        self.conn.execute("drop table if exists WordHidden")
        self.conn.execute("create table WordHidden(fromId, toId, strength)")

        self.conn.execute("drop table if exists HiddenUrl")
        self.conn.execute("create table HiddenUrl(fromId, toId, strength)")

        self.conn.commit()

    def getStrength(self, fromId, toId, layer):
        if layer == 0:
            table = "WordHidden"
        else:
            table = "HiddenUrl"

        result = self.conn.execute(
            "select strength from %s where fromId = %d and toId = %d" % (table, fromId, toId)).fetchone()

        if result is None:
            if layer == 0:
                return -0.2
            else:
                return 0
        else:
            return result[0]

    def setStrength(self, fromId, toId, layer, strength):
        if layer == 0:
            table = "WordHidden"
        else:
            table = "HiddenUrl"

        result = self.conn.execute(
            "select rowId from %s where fromId = %d and toId = %d" % (table, fromId, toId)).fetchone()

        if result is None:
            self.conn.execute("insert into %s(fromId, toId, strength) values (%d, %d, %f)" %
                              (table, fromId, toId, strength))
        else:
            self.conn.execute("update %s set strength = %f where rowId = %d" % (table, strength, result[0]))

    def generateHiddenNode(self, wordIds, urlIds):
        nWord = len(wordIds)

        if nWord > 3:
            return None

        # Check if we already created a node for this set of words
        createKey = '_'.join(sorted([str(wordId) for wordId in wordIds]))
        result = self.conn.execute("select rowId from HiddenNode where createKey = '%s'" % createKey).fetchone()

        # If not, create it
        if result is None:
            hiddenId = self.conn.execute("insert into HiddenNode(createKey) values ('%s')" % createKey).lastrowid

            # Put in some default weights
            for wordId in wordIds:
                self.setStrength(wordId, hiddenId, 0, 1.0 / nWord)
            for urlId in urlIds:
                self.setStrength(hiddenId, urlId, 1, 0.1)

            self.conn.commit()

    # find all the hidden nodes that are relevant to a specific query
    def getAllHiddenIds(self, wordIds, urlIds):
        hiddenIds = set()

        for wordId in wordIds:
            for (hiddenId,) in self.conn.execute("select toId from WordHidden where fromId = %d" % wordId):
                hiddenIds.add(hiddenId)

        for urlId in urlIds:
            for (hiddenId,) in self.conn.execute("select fromId from HiddenUrl where toId = %d" % urlId):
                hiddenIds.add(hiddenId)

        return [id for id in hiddenIds]

    def setupNetwork(self, wordIds, urlIds):
        # node lists
        self.wordIds = wordIds
        self.hiddenIds = self.getAllHiddenIds(wordIds, urlIds)
        self.urlIds = urlIds

        # node outputs
        self.wordOut = [1.0] * len(self.wordIds)
        self.hiddenOut = [1.0] * len(self.hiddenIds)
        self.urlOut = [1.0] * len(self.urlIds)

        # weight matrixes
        self.wordHidden = [[self.getStrength(wordId, hiddenId, 0) for hiddenId in self.hiddenIds]
                           for wordId in self.wordIds]
        self.hiddenUrl = [[self.getStrength(hiddenId, urlId, 1) for urlId in self.urlIds]
                          for hiddenId in self.hiddenIds]

    def feedForward(self):
        nIn = len(self.wordIds)
        nHidden = len(self.hiddenIds)
        nOut = len(self.urlIds)

        # the only inputs are the query words
        for i in range(nIn):
            self.wordOut[i] = 1.0

        # hidden activations
        for i in range(nHidden):
            sum = 0.0

            for j in range(nIn):
                sum += self.wordOut[j] * self.wordHidden[j][i]

            self.hiddenOut[i] = tanh(sum)

        # output activations
        for i in range(nOut):
            sum = 0.0

            for j in range(nHidden):
                sum += self.hiddenOut[j] * self.hiddenUrl[j][i]

            self.urlOut[i] = tanh(sum)

        return self.urlOut[:]

    def getResult(self, wordIds, urlIds):
        self.setupNetwork(wordIds, urlIds)
        return self.feedForward()

    def dTanh(self, y):
        return 1.0 - y * y

    def backPropagate(self, targets, rate=0.5):
        nIn = len(self.wordIds)
        nHidden = len(self.hiddenIds)
        nOut = len(self.urlIds)

        # calculate errors for output
        outputDeltas = [0.0] * nOut
        for i in range(nOut):
            error = targets[i] - self.urlOut[i]
            outputDeltas[i] = self.dTanh(self.urlOut[i]) * error

        # calculate errors for hidden layer
        hiddenDeltas = [0.0] * nHidden
        for i in range(nHidden):
            error = 0
            for j in range(nOut):
                error += outputDeltas[j] * self.hiddenUrl[i][j]
            hiddenDeltas[i] = self.dTanh(self.hiddenOut[i]) * error

        # update output weights
        for i in range(nHidden):
            for j in range(nOut):
                self.hiddenUrl[i][j] += rate * self.hiddenOut[i] * outputDeltas[j]

        # update input weights
        for i in range(nIn):
            for j in range(nHidden):
                self.wordHidden[i][j] += rate * self.wordOut[i] * hiddenDeltas[j]

    def trainQuery(self, wordIds, urlIds, selectedUrl):
        self.generateHiddenNode(wordIds, urlIds)
        self.setupNetwork(wordIds, urlIds)
        self.feedForward()

        targets = [0.0] * len(urlIds)
        targets[urlIds.index(selectedUrl)] = 1.0

        self.backPropagate(targets)
        self.updateDatabase()

    def updateDatabase(self):
        nIn = len(self.wordIds)
        nHidden = len(self.hiddenIds)
        nOut = len(self.urlIds)

        for i in range(nIn):
            for j in range(nHidden):
                self.setStrength(self.wordIds[i], self.hiddenIds[j], 0, self.wordHidden[i][j])

        for i in range(nHidden):
            for j in range(nOut):
                self.setStrength(self.hiddenIds[i], self.urlIds[j], 1, self.hiddenUrl[i][j])

        self.conn.commit()


def testNeuralNetwork():
    myNet = searchNet('NeuralNetwork.db')

    myNet.createTables()

    wWorld, wRiver, wBank = 101, 102, 103
    uWorldBank, uRiver, uEarth = 201, 202, 203
    allUrlIds = [uWorldBank, uRiver, uEarth]

    myNet.generateHiddenNode([wWorld, wBank], allUrlIds)
    for c in myNet.conn.execute('select * from WordHidden'):
        print c
    for c in myNet.conn.execute('select * from HiddenUrl'):
        print c

    print myNet.getResult([wWorld, wBank], allUrlIds)

    myNet.trainQuery([wWorld, wBank], allUrlIds, uWorldBank)
    print myNet.getResult([wWorld, wBank], allUrlIds)

    for i in range(30):
        myNet.trainQuery([wWorld, wBank], allUrlIds, uWorldBank)
        myNet.trainQuery([wRiver, wBank], allUrlIds, uRiver)
        myNet.trainQuery([wWorld], allUrlIds, uEarth)
    print myNet.getResult([wWorld, wBank], allUrlIds)
    print myNet.getResult([wRiver, wBank], allUrlIds)
    print myNet.getResult([wBank], allUrlIds)