from dinocr import Dinocr
from lxml.html import fromstring
from urllib2 import urlopen
import sys
import re
import twitter
from datetime import datetime
import smtplib
from cStringIO import StringIO
from email.mime.text import MIMEText
import webapp2
import logging




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
  # if datetime.now().year == 2014 and datetime.now().month == 4 and datetime.now().day <= 25:
  #  print "guest week"
  #   print msg
  #   sys.exit()
  if datetime.now().day == 1 and datetime.now().month == 4:
    print "april fool!"
    print msg
    sys.exit()
  if alert:
    # increment the comicnum so we don't get repeated alerts
    emsg = MIMEText(msg)
    emsg['Subject'] = 'trigramosaurus error!'
    emsg['From'] = 'kaytwo@kaytwo.org'
    emsg['To'] = 'kaytwo@gmail.com'
    # this smtp server might change but oh well...
    # s = smtplib.SMTP('gmail-smtp-in.l.google.com')
    # s.sendmail(emsg['From'],[emsg['To']],emsg.as_string())
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
    error_out("some sort of twitter error",True)
  return result

def update_comicnum(today):
  ''' read and return the comic number for today.
  regardless of errors, try to put today's comic number
  in the file.'''
  curnum = -1
  try:
    cn = open('trigramosaurus.txt','r+')
    try:
      curnum = int(cn.read().strip())
    except:
      pass
    cn.seek(0)
    cn.truncate()
    cn.write(str(today))
    cn.close()
    if curnum != -1:
      return curnum
    else:
      error_out("could not determine current comic number, reset it to %d" % today,True)
  except Exception as e:
    error_out("couldn't read comic number: "+e.message,True)

def main():
  comicid = ''
  today_comic = urlopen('http://www.qwantz.com/index.php' + comicid)
  result = today_comic.read()
  todayparsed = fromstring(result)
  try:
    comicurl = todayparsed.cssselect('img.comic')[0].attrib['src']
    comicnum = int(re.findall(r'comic2-([0-9]+)\.png',comicurl)[0])
  except Exception as e:
    print "failed parsing qwantz.com: " + e.message
  tmpfilep = StringIO()
  comic_image = urlopen(comicurl).read()
  tmpfilep.write(comic_image)
  tmpfilep.seek(0)
  logging.debug("wrote a file of length %d" % len(comic_image))
  d = Dinocr(tmpfilep)
  if d.erased_pixels > 2000:
    error_out('large amount of erases in a new comic (%d erases, %d uncertainty)' % (d.erased_pixels,d.uncertainty),True)
  trigram = d.choose_random_trigram()
  anything = False
  # don't acept a trigram that has a non-alphanumeric word in it
  if any([all([not x.isalnum() for x in word]) for word in trigram.split()]):
    error_out('words in this trigram are weird: %s' % trigram,True)
  return trigram
  # result = post_to_twitter(trigram)

class MainPage(webapp2.RequestHandler):
    def get(self):
        trigram = main()
        post_to_twitter(trigram)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(trigram)


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
