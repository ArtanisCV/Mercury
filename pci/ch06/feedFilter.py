import feedparser
import re

__author__ = 'Artanis'


# Takes a filename of URL of a blog feed and classifies the entries
def read(feed, classifier, useEntryFeatures=False):
    # Get feed entries and loop over them
    for entry in feedparser.parse(feed)['entries']:
        print
        print '-----'
        # Print the contents of the entry
        print 'Title: ' + entry['title'].encode('utf-8')
        print 'Publisher: ' + entry['publisher'].encode('utf-8')
        print
        print entry['summary'].encode('utf-8')

        # Combine all the text to create one item for the classifier
        fulltext = '%s\n%s\n%s' % (entry['title'], entry['publisher'], entry['summary'])

        # Print the best guess at the current category
        if useEntryFeatures is False:
            print 'Guess: ' + str(classifier.classify(fulltext))
        else:
            print 'Guess: ' + str(classifier.classify(entry))

        # Ask the user to specify the correct category and train on that
        category = raw_input('Enter category: ')

        if useEntryFeatures is False:
            classifier.train(fulltext, category)
        else:
            classifier.train(entry, category)


def entryFeatures(entry):
    splitter = re.compile(r'\W+')
    feature = {}

    # Extract the title words and annotate
    titleWords = [word.lower() for word in splitter.split(entry['title'])
                  if 2 < len(word) < 20]
    for word in titleWords:
        feature['Title:' + word] = 1

    # Extract the summary words
    summaryWords = [word for word in splitter.split(entry['summary'])
                    if 2 < len(word) < 20]

    # Count upper words
    uc = 0
    for i in range(len(summaryWords)):
        word = summaryWords[i]
        feature[word.lower()] = 1

        if word.isupper():
            uc += 1

        # Get word pairs in summary as features
        if i < len(summaryWords) - 1:
            twoWords = ' '.join(summaryWords[i: i + 1])
            feature[twoWords.lower()] = 1

    # Keep creator and publisher whole
    feature['Publisher:' + entry['publisher']] = 1

    # UPPERCASE is a virtual word flagging too much shouting
    if float(uc) / len(summaryWords) > 0.3:
        feature['UPPERCASE'] = 1

    return feature


def testFeedFilter():
    import docClass

    # cl = docClass.FisherClassifier(docClass.getWords)
    # cl.setDB('python_feed.db')
    #
    # read('python_search.xml', cl)
    #
    # print cl.cProb('python', 'prog')
    # print cl.cProb('python', 'snake')
    # print cl.cProb('python', 'monty')
    # print cl.cProb('eric', 'monty')
    # print cl.fProb('eric', 'monty')

    cl = docClass.FisherClassifier(entryFeatures)
    cl.setDB('python_feed.db')

    read('python_search.xml', cl, useEntryFeatures=True)
