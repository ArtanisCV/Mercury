from pydelicious import get_popular, get_userposts, get_urlposts
from pci.ch2 import recommendations
import random
import time

__author__ = 'Artanis'


def initializeUserDict(tag, count=5):
    user_dict = {}

    # get the top count' popular posts
    for postInfo in get_popular(tag=tag)[0:count]:

        # find all users who posted this
        for userInfo in get_urlposts(postInfo['url']):
            user = userInfo['user']

            if user != "":
                user_dict[user] = {}

    return user_dict


def fillItems(user_dict):
    all_items = []

    # find links posted by all users
    for user in user_dict:
        posts = None

        for i in range(3):
            try:
                posts = get_userposts(user)
                break
            except:
                print "Failed user "+user+", retrying"
                time.sleep(4)

        if posts is not None:
            for postInfo in posts:
                url = postInfo['url']
                user_dict[user][url] = 1.0
                all_items.append(url)

    for item in all_items:
        for ratings in user_dict.values():
            if item not in ratings:
                ratings[item] = 0.0


def testDelicious():
    delusers = initializeUserDict('programming')
    fillItems(delusers)

    user = delusers.keys()[random.randint(0, len(delusers))]
    print user
    print recommendations.topMatches(delusers, user, similarity=recommendations.sim_euclidean)
    recUrls = recommendations.getRecommendations(delusers, user, similarity=recommendations.sim_euclidean)[0:10]
    print recUrls

    url = recUrls[0][1]
    print url
    print recommendations.topMatches(recommendations.transformPrefs(delusers), url)