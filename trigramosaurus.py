import cgi
import datetime
import urllib
import webapp2

from google.appengine.api import conversion
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images

class Comic(db.Model):
  """Models the information you need to store to render today's comic"""
  comic = db.Blob()
  comic_filename = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  last_check = db.DateTimeProperty(auto_now_add=True)
  text = db.StringProperty()


class Greeting(db.Model):
  """Models an individual Guestbook entry with an author, content, and date."""
  author = db.StringProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)


def guestbook_key(guestbook_name=None):
  """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
  return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')


class MainPage(webapp2.RequestHandler):
  def get(self):
    # testing: use pre-masked image
    blank_comic = open('blank_comic.png').read()
    # crop to one frame
    width = float(735)
    height = float(500)
    img = images.Image(blank_comic)
    # panel 1
    # img.crop(0.0,0.0,242/width,242/height)
    img.crop(374/width,0.0,735/width,55/height)
    img.resize(600)
    blank_comic = img.execute_transforms()
    # self.response.headers['Content-Type'] = 'image/png'
    # self.response.out.write(blank_comic)
    asset = conversion.Asset("image/png",blank_comic,'blank_comic.png')
    conversion_obj = conversion.Conversion(asset,'text/plain')
    result = conversion.convert(conversion_obj)
    if result.assets:
      for asset in result.assets:
        self.response.out.write(asset.data)
    else:
      self.response.out.write(str(result.error_code) + ' ' + result.error_text)

class CronJob(webapp2.RequestHandler):
  def get(self):
    """check for a new comic and if one exists, perform the
    transformations needed to update the main page."""
    # pull most recent comic info from datastore

    # don't check if we fond a comic within the last 20 hours
    
    # download html for qwantz.com

    # extract comic image url

    # compare to previous day's comic's filename,
    # abort if today's < prev's (classic comix)

    # download comic image

    # extract text

    # choose random 3 words

    # post to twitter via oauth?


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/check', CronJob)],
                              debug=True)



class ImageManipulations:
    def mask_characters(self,comic):
        """take a binary blob of a comic and mask away the static
        character images, returning the new binary blob image"""
        f = open('white.mask.png').read()
        # g = open('comic.png').read()
        g = comic
        im1 = images.Image(g)
        im2 = images.Image(f)
        composite = images.composite([(im1,0,0,1.0,images.TOP_LEFT),
        (im2,0,0,1.0,images.TOP_LEFT)],735,500,images.PNG)
        return composite
        # self.response.headers['Content-Type'] = 'image/png'
        # self.response.out.write(composite)
        # self.response.out.write('Hello, webapp World!')

