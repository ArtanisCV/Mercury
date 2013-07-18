import urllib2
import re
from BeautifulSoup import BeautifulSoup

__author__ = 'Artanis'


def testBeautifulSoup():
    file = urllib2.urlopen('http://kiwitobes.com/wiki/Programming_language.html')
    soup = BeautifulSoup(file.read())
    links = soup('a')
    print links[10]
    print links[10]['href']


def downloadZeboData():
    chare = re.compile(r'[!-\.&]')
    itemOwners = {}
    currentUser = 0

    # Words to remove
    dropWords = ['a', 'new', 'some', 'more', 'my', 'own', 'the', 'many', 'other', 'another']

    for i in range(1, 51):
        # URL for the "want" search page
        file = urllib2.urlopen('http://member.zebo.com/Main?event_key=USERSEARCH&wiowiw=wiw&keyword=car&page=%d' % i)
        soup = BeautifulSoup(file.read())

        for td in soup('td'):
            # Find table cells of bgverdanasmall class
            if 'class' in dict(td.attrs) and td['class'] == 'bgverdanasmall':
                items = [re.sub(chare, '', a.contents[0].lower()).strip() for a in td('a')]

                for item in items:
                    # Remove extra words
                    text = ' '.join([t for t in item.split(' ') if t not in dropWords])
                    if len(text) < 2:
                        continue

                    itemOwners.setdefault(text, {})
                    itemOwners[text][currentUser] = 1

                currentUser += 1

    out = file('zeboData-tmp.txt', 'w')

    out.write('Item')
    for user in range(currentUser):
        out.write('\tU%d' % user)
    out.write('\n')

    for (item, owners) in itemOwners.items():
        if len(owners) > 10:
            out.write(item)
            for user in range(currentUser):
                if user in owners:
                    out.write('\t1')
                else:
                    out.write('\t0')
            out.write('\n')