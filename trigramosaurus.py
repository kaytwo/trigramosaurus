from dinocr import Dinocr
from lxml.html import fromstring
from urllib2 import urlopen
from os import system
import sys
import re
import twitter

import smtplib
from email.mime.text import MIMEText


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



def error_out(msg,alert=False):
  if alert:
    # increment the comicnum so we don't get repeated alerts
    update_comicnum()
    emsg = MIMEText(msg)
    emsg['Subject'] = 'trigramosaurus error!'
    emsg['From'] = 'kaytwo@kaytwo.org'
    emsg['To'] = 'kaytwo@gmail.com'
    # this smtp server might change but oh well...
    s = smtplib.SMTP('gmail-smtp-in.l.google.com')
    s.sendmail(emsg['From'],[emsg['To']],emsg.as_string())
  else:
    print msg
  sys.exit()

def post_to_twitter(msg):
  '''
  todo:
  check if trigramosaurus has been updated today, if so, skip updating.
  '''
  oauth_token, oauth_secret = twitter.read_token_file('trigramosaurus_credentials')
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

def update_comicnum():
  cn = open('trigramosaurus.txt','r+')
  curnum = int(cn.read().strip())
  cn.truncate()
  cn.write(str(curnum+1))
  cn.close()

if __name__ == "__main__":
  trigram_info = open('trigramosaurus.txt','r')
  prev_comic = int(trigram_info.read().strip())
  trigram_info.close()
  today_comic = urlopen('http://www.qwantz.com/index.php')
  result = today_comic.read()
  todayparsed = fromstring(result)
  try:
    comicurl = todayparsed.cssselect('img.comic')[0].attrib['src']
    comicnum = int(re.findall(r'comic2-([0-9]+)\.png',comicurl)[0])
  except IndexError:
    error_out("failed parsing qwantz.com",True)
  if comicnum == prev_comic:
    error_out("same comic")
  if comicnum != prev_comic + 1:
    error_out("unexpected comic number: previous was %d, this was %d" % (prev_comic,comicnum),True)
  system('curl %s > /tmp/comic.png' % comicurl)
  d = Dinocr('/tmp/comic.png')
  if d.erased_pixels > 2000:
    error_out('large amount of erases in a new comic',True)
  trigram = d.choose_random_trigram()
  anything = False
  for word in trigram.split():
    if any([x.isalnum() for x in word]):
      anything = True
      break
  if not anything:
    error_out('words in this trigram are weird: %s' % trigram,True)
  result = post_to_twitter(trigram)
  infofile = open('trigramosaurus.txt','w')
  infofile.write(str(comicnum))
  infofile.close()
