from dinocr import Dinocr
from lxml.html import fromstring, HtmlComment
from lxml import etree
from urllib2 import urlopen
from os import system
import sys
import re
import twitter
from StringIO import StringIO

import smtplib
from email.mime.text import MIMEText
from multiprocessing import Pool

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


def xml_compare(x1, x2, reporter=lambda x: sys.stdout.write(x + '\n')):
    if x1.tag != x2.tag:
        if reporter:
            reporter('Tags do not match: %s and %s' % (x1.tag, x2.tag))
        return False
    for name, value in x1.attrib.items():
        if x2.attrib.get(name) != value:
            if reporter:
                reporter('Attributes do not match: %s=%r, %s=%r'
                         % (name, value, name, x2.attrib.get(name)))
            return False
    for name in x2.attrib.keys():
        if name not in x1.attrib:
            if reporter:
                reporter('x2 has an attribute x1 is missing: %s'
                         % name)
            return False
    if not text_compare(x1.text, x2.text):
        if reporter:
            reporter('text: %r != %r' % (x1.text, x2.text))
        return False
    if not text_compare(x1.tail, x2.tail):
        if reporter:
            reporter('tail: %r != %r' % (x1.tail, x2.tail))
        return False
    cl1 = x1.getchildren()
    cl2 = x2.getchildren()
    if len(cl1) != len(cl2):
        if reporter:
            reporter('children length differs, %i != %i'
                     % (len(cl1), len(cl2)))
        return False
    i = 0
    for c1, c2 in zip(cl1, cl2):
        i += 1
        if not xml_compare(c1, c2, reporter=reporter):
            if reporter:
                reporter('children %i do not match: %s'
                         % (i, c1.tag))
            return False
    return True


def text_compare(t1, t2):
    if not t1 and not t2:
        return True
    if t1 == '*' or t2 == '*':
        return True
    return (t1 or '').strip() == (t2 or '').strip()

answers = {}
t = etree.parse(open('everywordindinosaurcomicsOHGOD.xml'))
for item in t.findall('transcription'):
  answers[item[0].text] = item # etree.tostring(item, pretty_print=True)

def compare_with_old_transcription(comicnum=1):
  comic_url = 'http://www.qwantz.com/index.php?comic=' + str(comicnum)
  xml_url = comic_url[11:]
  today_comic = urlopen(comic_url)
  result = today_comic.read()
  todayparsed = fromstring(result)
  try:
    imageurl = todayparsed.cssselect('img.comic')[0].attrib['src']
    comicnum = int(re.findall(r'comic2-([0-9]+)\.png',imageurl)[0])
    comic_title = 'unknown'
    for comment in [element for element in todayparsed.iter() if isinstance(element,HtmlComment)]:
      t = fromstring(comment.text_content()).cssselect('.rss-title')
      if len(t) != 0:
        comic_title = t[0].text_content()
  except IndexError:
    error_out("failed parsing qwantz.com",False)
  system('curl %s > /tmp/comic.png' % imageurl)
  d = Dinocr('/tmp/comic.png',title=comic_title,url=xml_url)
  d.print_comic()
  d.generate_old_xml()
  print xml_url
  xml_compare(d.old_xml, answers[xml_url])

def create_transcription(comicnum=1):
  comic_url = 'http://www.qwantz.com/index.php?comic=' + str(comicnum)
  xml_url = comic_url[11:]
  today_comic = urlopen(comic_url)
  result = today_comic.read()
  todayparsed = fromstring(result)
  subject_text = 'unknown'
  mouseover_text = 'unknown'
  try:
    imageurl = todayparsed.cssselect('img.comic')[0].attrib['src']
    mouseover_text = todayparsed.cssselect('img.comic')[0].attrib['title']
    comicnum = int(re.findall(r'comic2-([0-9]+)\.png',imageurl)[0])
    comic_title = 'unknown'
    for comment in [element for element in todayparsed.iter() if isinstance(element,HtmlComment)]:
      t = fromstring(comment.text_content()).cssselect('.rss-title')
      if len(t) != 0:
        comic_title = t[0].text_content()
    for item in todayparsed.cssselect('li'):
      if item.text_content() == 'contact':
        subject_text = item[0].attrib['href'].split('=')[1]
  except IndexError:
    return None
  img = StringIO(urlopen(imageurl).read())

  d = Dinocr(img,title=comic_title,url=xml_url,subject_text=subject_text,mouseover_text=mouseover_text)
  return d.string_new_xml()



if __name__=='__main__':
  comicnums = [1,2]
  if len(sys.argv) == 3:
    comicnums = range(int(sys.argv[1]),int(sys.argv[2]))
  results = []
  for c in comicnums:
    print create_transcription(c),
