import akismet

__author__ = 'Artanis'

defaultKey = "YOURKEYHERE"
pageUrl = "http://yoururlhere.com"

defaultAgent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.7) "
defaultAgent += "Gecko/20060909 Firefox/1.5.0.7"


def isSpam(comment, author, ipAddress, agent=defaultAgent, apiKey=defaultKey):
    try:
        valid = akismet.verify_key(apiKey, pageUrl)
        if valid:
            return akismet.comment_check(apiKey, pageUrl, ipAddress, agent,
                                         comment_content=comment,
                                         comment_author_email=author,
                                         comment_type="comment")
        else:
            print 'Invalid key'
            return False
    except akismet.AkismetError, e:
        print e.response, e.statuscode
        return False


def testAkismet():
    msg = 'Make money fast! Online Casino!'
    print isSpam(msg, 'spammer@spam.com', '127.0.0.1')