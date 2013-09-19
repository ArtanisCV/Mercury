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
        self.fc.setdefault(feature, {})
        self.fc[feature].setdefault(category, 0)
        self.fc[feature][category] += 1

    # Increase the count of a category
    def incC(self, category):
        self.cc.setdefault(category, 0)
        self.cc[category] += 1

    # The number of times a feature has appeared in a category
    def fCount(self, feature, category):
        if feature in self.fc and category in self.fc[feature]:
            return float(self.fc[feature][category])
        return 0.0

    # The number of items in a category
    def catCount(self, category):
        if category in self.cc:
            return float(self.cc[category])
        return 0.0

    # The total number of items
    def totalCount(self):
        return sum(self.cc.values())

    # The list of all categories
    def categories(self):
        return self.cc.keys()

    def train(self, item, category):
        features = self.getFeatures(item)

        # Increment the count for every feature with this category
        for feature in features:
            self.incF(feature, category)

        # Increment the count for this category
        self.incC(category)

    def fProb(self, feature, category):
        if self.catCount(category) == 0:
            return 0

        # The total number of times this feature appeared in this
        # category divided by the total number of items in this category
        return self.fCount(feature, category) / self.catCount(category)

    def weightedProb(self, feature, category, fp, weight=1.0, ap=0.5):
        # Calculate current probability
        basicProb = fp(feature, category)

        # Count the number of times this feature has appeared in all categories
        totals = sum([self.fCount(feature, category)
                      for category in self.categories()])

        # Calculate the weighted average
        bp = ((weight * ap) + (totals * basicProb)) / (weight + totals)
        return bp


class NaiveBayes(Classifier):
    def __init__(self, getFeatures):
        Classifier.__init__(self, getFeatures)
        self.thresholds = {}

    def docProb(self, doc, category):
        features = self.getFeatures(doc)

        # Multiply the probabilities of all the features together
        p = 1
        for feature in features:
            p *= self.weightedProb(feature, category, self.fProb)

        return p

    def prob(self, doc, category):
        catProb = self.catCount(category) / self.totalCount()
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
        max = 0.0
        for category in self.categories():
            probs[category] = self.prob(doc, category)
            if probs[category] > max:
                max = probs[category]
                best = category

        # Make sure the probability exceeds threshold * next best
        for category in self.categories():
            if category == best:
                continue
            if probs[category] * self.getThreshold(best) > probs[best]:
                return default

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
