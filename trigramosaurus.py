from dinocr import Dinocr
from lxml.html import fromstring
from urllib2 import urlopen
from os import system
import sys
import re
import twitter
from pprint import pprint

'''
script to automatically update trigramosaurus

if anything ever goes wrong, email me instead

unpickle previous_comic info
pull qwantz.com
parse for filename
parse filename
if comic # is prev + 1, continue
wget comic
Dinocr
post to twitter
'''

def error_out(msg):
  print msg
  sys.exit()

def post_to_twitter(msg):
  oauth_token, oauth_secret = twitter.read_token_file('kaytwo_credentials')
  consumer_key, consumer_secret = twitter.read_token_file('app_credentials')
  t = twitter.Twitter(
            auth=twitter.OAuth(oauth_token, oauth_secret,
                       consumer_key, consumer_secret)
           )
  try:
    result = t.statuses.update(status=msg)
  # invalid status causes twitter.api.TwitterHTTPError
  except:
    error_out("some sort of twitter error")
  return result

if __name__ == "__main__":
  trigram_info = open('trigramosaurus.txt','r')
  prev_comic = int(trigram_info.read().strip())
  trigram_info.close()
  today_comic = urlopen('http://www.qwantz.com/index.php')
  result = today_comic.read()
  todayparsed = fromstring(result)
  comicurl = todayparsed.cssselect('img.comic')[0].attrib['src']
  comicnum = int(re.findall(r'comic2-([0-9]+)\.png',comicurl)[0])
  if comicnum == prev_comic:
    error_out("same comic")
  if comicnum != prev_comic + 1:
    error_out("unexpected comic number: previous was %d, this was %d" % (prev_comic,comicnum))
  system('curl %s > /tmp/comic.png' % comicurl)
  trigram = Dinocr('/tmp/comic.png').choose_random_trigram()
  result = post_to_twitter(trigram)
  infofile = open('trigramosaurus.txt','w')
  infofile.write(str(comicnum))
  infofile.close()
