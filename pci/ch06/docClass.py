from pysqlite2 import dbapi2 as sqlite
import re
import math

__author__ = 'Artanis'


def getWords(doc):
    splitter = re.compile(r'\W+')

    # Split thw words by non-alpha characters
    words = [word.lower() for word in splitter.split(doc)
             if 2 < len(word) < 20]

    # Return the unique set of words only
    return dict([(word, 1) for word in words])


class Classifier:
    def __init__(self, getFeatures):
        # Counts of feature/category combinations
        self.fc = {}

        # Counts of documents in each category
        self.cc = {}

        self.getFeatures = getFeatures

    # Increase the count of a feature/category pair
    def incF(self, feature, category):
        if hasattr(self, 'conn'):
            count = self.fCount(feature, category)
            if count == 0:
                self.conn.execute("insert into fc values ('%s', '%s', 1)" %
                                  (feature, category))
            else:
                self.conn.execute("update fc set count=%d where feature='%s' and category='%s'" %
                                  (count + 1, feature, category))
        else:
            self.fc.setdefault(feature, {})
            self.fc[feature].setdefault(category, 0)
            self.fc[feature][category] += 1

    # Increase the count of a category
    def incC(self, category):
        if hasattr(self, 'conn'):
            count = self.cCount(category)
            if count == 0:
                self.conn.execute("insert into cc values ('%s', 1)" % category)
            else:
                self.conn.execute("update cc set count=%d where category='%s'" %
                                  (count + 1, category))
        else:
            self.cc.setdefault(category, 0)
            self.cc[category] += 1

    # The number of times a feature has appeared in a category
    def fCount(self, feature, category):
        if hasattr(self, 'conn'):
            result = self.conn.execute("select count from fc where feature='%s' and category='%s'" %
                                       (feature, category)).fetchone()
            if result is None:
                return 0.0
            else:
                return float(result[0])
        else:
            if feature in self.fc and category in self.fc[feature]:
                return float(self.fc[feature][category])
            else:
                return 0.0

    # The number of items in a category
    def cCount(self, category):
        if hasattr(self, 'conn'):
            result = self.conn.execute("select count from cc where category='%s'" %
                                       category).fetchone()
            if result is None:
                return 0.0
            else:
                return float(result[0])
        else:
            if category in self.cc:
                return float(self.cc[category])
            else:
                return 0.0

    # The total number of items
    def totalCount(self):
        if hasattr(self, 'conn'):
            result = self.conn.execute("select sum(count) from cc").fetchone()
            if result is None:
                return 0.0
            else:
                return result[0]
        else:
            return sum(self.cc.values())

    # The list of all categories
    def categories(self):
        if hasattr(self, 'conn'):
            cursor = self.conn.execute('select category from cc')
            return [item[0] for item in cursor]
        else:
            return self.cc.keys()

    def train(self, item, category):
        features = self.getFeatures(item)

        # Increment the count for every feature with this category
        for feature in features:
            self.incF(feature, category)

        # Increment the count for this category
        self.incC(category)

        if hasattr(self, 'conn'):
            self.conn.commit()

    def fProb(self, feature, category):
        if self.cCount(category) == 0:
            return 0

        # The total number of times this feature appeared in this
        # category divided by the total number of items in this category
        return self.fCount(feature, category) / self.cCount(category)

    def weightedProb(self, feature, category, fProb, weight=1.0, ap=0.5):
        # Calculate current probability
        fp = fProb(feature, category)

        # Count the number of times this feature has appeared in all categories
        totals = sum([self.fCount(feature, category)
                      for category in self.categories()])

        # Calculate the weighted average
        bp = ((weight * ap) + (totals * fp)) / (weight + totals)
        return bp

    def setDB(self, dbFile):
        self.conn = sqlite.connect(dbFile)
        self.conn.execute('create table if not exists fc(feature, category, count)')
        self.conn.execute('create table if not exists cc(category, count)')


class NaiveBayes(Classifier):
    def __init__(self, getFeatures):
        Classifier.__init__(self, getFeatures)
        self.thresholds = {}

    def docProb(self, doc, category):
        # Multiply the probabilities of all the features together
        p = 1
        for feature in self.getFeatures(doc):
            p *= self.weightedProb(feature, category, self.fProb)

        return p

    def prob(self, doc, category):
        catProb = self.cCount(category) / self.totalCount()
        docProb = self.docProb(doc, category)

        return catProb * docProb

    def setThreshold(self, category, threshold):
        self.thresholds[category] = threshold

    def getThreshold(self, category):
        if category not in self.thresholds:
            return 1.0
        return self.thresholds[category]

    def classify(self, doc, default=None):
        probs = {}

        # Find the category with the highest probability
        maxProb = 0.0
        for category in self.categories():
            probs[category] = self.prob(doc, category)
            if probs[category] > maxProb:
                maxProb = probs[category]
                best = category

        # Make sure the probability exceeds threshold * next best
        for category in self.categories():
            if category == best:
                continue
            if probs[category] * self.getThreshold(best) > probs[best]:
                return default

        return best


class FisherClassifier(Classifier):
    def __init__(self, getFeatures):
        Classifier.__init__(self, getFeatures)
        self.minimums = {}

    def cProb(self, feature, category):
        # The frequency of this feature in this category
        clf = self.fProb(feature, category)
        if clf == 0:
            return 0

        # The frequency of this feature in all the categories
        freqSum = sum([self.fProb(feature, category)
                       for category in self.categories()])

        # The probability is the frequency in this category divided by
        # the overall frequency
        p = clf / freqSum
        return p

    def fisherProb(self, doc, category):
        features = self.getFeatures(doc)

        # Multiply all the probabilities together
        p = 1
        for feature in features:
            p *= self.weightedProb(feature, category, self.cProb)

        # Take the natural log and multiply by -2
        fScore = -2 * math.log(p)

        # Use the inverse chi2 function to get a probability
        return self.invChi2(fScore, len(features) * 2)

    def invChi2(self, chi, df):
        m = chi / 2.0
        total = term = math.exp(-m)

        for i in range(1, df // 2):
            term *= m / i
            total += term

        return min(total, 1.0)

    def setMinimum(self, category, minimum):
        self.minimums[category] = minimum

    def getMinimum(self, category):
        if category not in self.minimums:
            return 0
        return self.minimums[category]

    def classify(self, doc, default=None):
        # Loop through looking for the best result
        best = default
        maximum = 0.0

        for category in self.categories():
            p = self.fisherProb(doc, category)

            # Make sure it exceeds its minimum
            if p > self.getMinimum(category) and p > maximum:
                maximum = p
                best = category

        return best


def sampleTrain(cl):
    cl.train('Nobody owns the water.', 'good')
    cl.train('the quick rabbit jumps fences', 'good')
    cl.train('buy pharmaceuticals now', 'bad')
    cl.train('make quick money at the online casino', 'bad')
    cl.train('the quick brown fox jumps', 'good')


def testDocClass():
    cl = Classifier(getWords)
    cl.train('the quick brown fox jumps over the lazy dog', 'good')
    cl.train('make quick money in the online casino', 'bad')
    print cl.fCount('quick', 'good')
    print cl.fCount('quick', 'bad')

    cl = Classifier(getWords)
    sampleTrain(cl)
    print cl.fProb('quick', 'good')

    cl = Classifier(getWords)
    sampleTrain(cl)
    print cl.weightedProb('money', 'good', cl.fProb)
    sampleTrain(cl)
    print cl.weightedProb('money', 'good', cl.fProb)

    cl = NaiveBayes(getWords)
    sampleTrain(cl)
    print cl.prob('quick rabbit', 'good')
    print cl.prob('quick rabbit', 'bad')

    cl = NaiveBayes(getWords)

    sampleTrain(cl)
    print cl.classify('quick rabbit', default='unknown')
    print cl.classify('quick money', default='unknown')

    cl.setThreshold('bad', 3.0)
    print cl.classify('quick money', default='unknown')

    for i in range(10):
        sampleTrain(cl)
    print cl.classify('quick money', default='unknown')

    cl = FisherClassifier(getWords)
    sampleTrain(cl)
    print cl.cProb('quick', 'good')
    print cl.cProb('money', 'bad')
    print cl.weightedProb('money', 'bad', cl.cProb)

    cl = FisherClassifier(getWords)
    sampleTrain(cl)
    print cl.cProb('quick', 'good')
    print cl.fisherProb('quick rabbit', 'good')
    print cl.fisherProb('quick rabbit', 'bad')

    sampleTrain(cl)
    print cl.classify('quick rabbit')
    print cl.classify('quick money')

    cl.setMinimum('bad', 0.8)
    print cl.classify('quick money')

    cl.setMinimum('good', 0.4)
    print cl.classify('quick money')

    cl = FisherClassifier(getWords)
    cl.setDB('test.db')
    sampleTrain(cl)

    cl = NaiveBayes(getWords)
    cl.setDB('test.db')
    print cl.classify('quick money')