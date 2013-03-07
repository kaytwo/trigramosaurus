# vim: set fileencoding=utf-8

import sys
import pickle
from collections import defaultdict
import Image, StringIO, sqlite3
from lxml import etree
from operator import itemgetter

''' helper functions'''

def printmap(s):
  offset = 0
  for y in range(13):
    for x in range(8):
      if s[offset] >= 1:
        sys.stdout.write(' ')
      else:
        sys.stdout.write('X')
      offset += 1
    print ""

def printmap_bold(s):
  offset = 0
  for y in range(13):
    for x in range(9):
      if s[offset] >= 1:
        sys.stdout.write(' ')
      else:
        sys.stdout.write('X')
      offset += 1
    print ""


def print_prospective_bold(img,x,y):
  for y1 in range(13):
    for x1 in range(9):
      if img[x+x1,y+y1] > 0:
        sys.stdout.write(' ')
      else:
        sys.stdout.write('X')
    print ""

def print_prospective(pix):
  for y in range(13):
    for x in range(8):
      if pix[x,y] > 0:
        sys.stdout.write(' ')
      else:
        sys.stdout.write('X')
    print ""

class UnsureException(Exception):
  '''raise this when parsing fails enough
  that the comic should be looked at by a human
  instead.'''

  def __init__(self,value):
    self.value=value

  def __str__(self):
    return repr(self.value)


class Stanza:
  def __init__(self,words,text_color,color,is_bold=False,is_italic=False):
    self.speaker = 'unknown'
    self.text_color = text_color
    self.words = words
    self.color = color
    self.is_bold = is_bold
    self.is_italic = is_italic
  
  def __str__(self):
      return unicode(self).encode('utf-8')
  
  def __unicode__(self):
    return "%-15s%s" % (self.speaker + ':',' '.join(''.join(self.words).split()))

  def text(self):
    return ' '.join(''.join(self.words).split())

class DinosaurComicPanel:
  def __init__(self):
    self.stanzas = []
    self.panel_number = -1

  def __str__(self):
      return unicode(self).encode('utf-8')
 
  def __unicode__(self):
    return 'Panel %d:\n' % self.panel_number + \
      '\n'.join([unicode(x) for x in self.stanzas])

  def text(self):
    return ' '.join([x.text() for x in self.stanzas])


class DinosaurComic:
  def __init__(self,name='unknown'):
    self.curpanel = 1
    self.panels = []
    self.name = name

  def addpanel(self,panel):
    panel.panel_number = self.curpanel
    self.panels.append(panel)
    self.curpanel += 1

  def text(self):
    return ' '.join([x.text() for x in self.panels])
  
  def __str__(self):
      return unicode(self).encode('utf-8')
 
  def __unicode__(self):
    return 'comic %s\n' % self.name + \
      '\n'.join([unicode(x) for x in self.panels])

  def stanzas(self):
    for panel in self.panels:
      for stanza in panel.stanzas:
        yield stanza

'''
how to use the object representations:
  
  thisComic = DinosaurComic()

  for blahblah:
    thisPanel = DinosaurComicPanel()
    stanzas = []
    stanzas.append(Stanza(foundwords, colorctr))
    stanzas.append(Stanza(foundwords, colorctr))
    thisPanel.stanzas = stanzas
    thisComic.append(thisPanel)
'''

class Dinocr:
  charmap_file = open('charmap.pkl','rb')
  charmap_bold = open('charmap_bold.pkl','rb')
  charmap_italic = open('charmap_italic.pkl','rb')
  

  @staticmethod
  def printascii(s):
    for letter in s:
      big = Dinocr.charmap[letter]
      offset = 0
      for y in range(13):
        for x in range(8):
          if big[0][offset] == 1:
            sys.stdout.write(' ')
          else:
            sys.stdout.write('X')
          offset += 1
        print ""
      print ""
    
  colors = {
     (0, 38, 255, 255): 'Dromiceiomimus',
     (0, 148, 255, 255): 'House',
     (0, 255, 33, 255): 'Utahraptor',
     (0, 255, 255, 255): 'T-Rex',
     # (128, 0, 0, 255): 'Devil',
     (128, 128, 128, 255): 'Ryan',
     (255, 0, 255, 255): 'border',
     (255, 106, 0, 255): 'Girl',
     (255, 216, 0, 255): 'Car',
     (123,123,123,255): 'ERROR'
     }
 
  textcolors = {
      (0x80,0,0,0xFF):'red',
      (107,3,0,255):'red',
      (0,0,0,0xFF):'normal'
      }

  italic_charmap = pickle.load(charmap_italic)
  italic_revmap = pickle.load(charmap_italic)

  bold_charmap = pickle.load(charmap_bold)
  bold_revmap = pickle.load(charmap_bold)

  charmap = pickle.load(charmap_file)
  revmap = pickle.load(charmap_file)

  italic_offset = [3,3,3,2,2,2,1,1,1,0,0,-1,-1]

  def find_first_pixel(self,bbox):
    '''find the first black/devil pixel scanning LR and TB'''
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    startx = bbox[0]
    starty = bbox[1]
    this_line = []
    for y in range(height):
      for x in range(width):
        thispix = self.pix[x+startx,y+starty]
        if thispix in Dinocr.colors or \
           thispix in self.stanza_colors or \
           thispix == (255,255,255,255):
          continue
        # if thispix in Dinocr.textcolors:
        return startx+x,starty+y
    return -1,-1
  
  
  def should_erase(self,color):
    if color in Dinocr.colors or color == (255,255,255,255) \
        or color in self.stanza_colors:
      return False
    return True

  def erase_contiguous(self,x,y):
    '''
    recursively blank every non-white, non-border pixel
    that is adjacent to this pixel

    increase uncertainty if any of the pixels is not black or devil color.

    return None if bbox doesn't work out or color not (black/devil). 
    this is evidence the blob isn't a callout.
    '''
    erased = []
    # minx, miny, maxx, maxy
    bbox = [-1,-1,-1,-1]
    this_pixel_color = self.pix[x,y]
    miny = (x,y)
    maxy = (x,y)
    bbox = [x,y,x,y]
    pending_wipe = [(x,y)]
    while len(pending_wipe) > 0:
      x,y = pending_wipe.pop()
      erased.append((x,y))
      if y < bbox[1]:
        bbox[1] = y
      if y > bbox[3]:
        bbox[3] = y
      if x < bbox[0]:
        bbox[0] = x
      if x > bbox[2]:
        bbox[2] = x
      if self.pix[x,y] not in Dinocr.textcolors and self.pix[x,y] != (255,255,255,255):
        # print "increased uncertainty because i erased color:",self.pix[x,y]
        self.uncertainty += 1
        self.pix[x,y] = (255,0,255,255)
      else:
        self.pix[x,y] = (255,255,255,255)
      self.erased_pixels += 1
      try:
        if self.should_erase(self.pix[x-1,y]):
          pending_wipe.append((x-1,y))
        if self.should_erase(self.pix[x+1,y]):
          pending_wipe.append((x+1,y))
        if self.should_erase(self.pix[x,y-1]):
          pending_wipe.append((x,y-1))
        if self.should_erase(self.pix[x,y+1]):
          pending_wipe.append((x,y+1))
      except IndexError:
        continue
    if (bbox[0],bbox[1]) in erased and (bbox[2],bbox[3]) in erased:
      return (bbox[0],bbox[1]),(bbox[2],bbox[3])
    elif (bbox[0],bbox[3]) in erased and (bbox[2],bbox[1]) in erased:
      return (bbox[0],bbox[3]),(bbox[2],bbox[1])
    # print "increased uncertainty because of bad bbox on erase:",bbox
    self.uncertainty += 1
    return None

  def erase_bold_character_area(self,x,y,color):
    '''blank the 9x13 area starting at (x,y)'''
    for y1 in range(13):
      for x1 in range(9):
        try:
          self.pix[x+x1,y+y1] = color
        except IndexError:
          continue

  def erase_italic_character_area(self,x,y,color):
    '''blank the 8x13 area starting at (x,y)'''
    for y1 in range(13):
      for x1 in range(8):
        try:
          self.pix[x+x1 + Dinocr.italic_offset[y1],y+y1] = color
        except IndexError:
          continue

  def erase_character_area(self,x,y,color):
    '''blank the 8x13 area starting at (x,y)'''
    for y1 in range(13):
      for x1 in range(8):
        try:
          self.pix[x+x1,y+y1] = color
        except IndexError:
          continue
  def match_with_italic_character(self,x,y,origin=False,erase_color=(255,255,255,255)):
    '''
    with origin = true, (x,y) denotes the origin of where we expect
    the character to be; 
    with origin = false, (x,y) is the first 
    colored character found, and we must find the prospective origin
    to make the comparison
    '''
    old_color = None
    if origin == True:
      new_char = []
      for y1 in range(13):
        for x1 in range(8):
          try:
            if self.pix[x + x1 + Dinocr.italic_offset[y1],
                y + y1] in self.textcolors.keys():
              old_color = self.pix[x + x1 + Dinocr.italic_offset[y1],y + y1]
              c = 0
            else:
              c = 1
            new_char.append(c)
          except IndexError:
            new_char.append(1)
      if tuple(new_char) in Dinocr.italic_revmap:
        self.erase_italic_character_area(x,y,erase_color)
        return (Dinocr.italic_revmap[tuple(new_char)],old_color),x,y
      else:
        return (' ',None),-1,-1
    
    # origin == False
    for letter in Dinocr.italic_charmap.keys():
      offsetx,offsety = Dinocr.italic_charmap[letter][1:]
      letter_start_x = x - offsetx - Dinocr.italic_offset[offsety]
      letter_start_y = y - offsety
      if letter_start_x < 0 or letter_start_y < 0:
        continue
      # print("searching for exact match with %s at %d,%d" % 
      #       (letter,letter_start_x,letter_start_y))
      new_char = []
      for y1 in range(13):
        for x1 in range(8):
          try:
            if self.pix[letter_start_x + x1 + Dinocr.italic_offset[y1],
                        letter_start_y + y1] in self.textcolors.keys():
              old_color = self.pix[letter_start_x + x1 + Dinocr.italic_offset[y1], \
                                   letter_start_y + y1] 
              c = 0
            else:
              c = 1
            new_char.append(c)
          except IndexError:
            new_char.append(1)

      # printmap(new_char)
      if all([(new_char[a] > 0) == 
              (Dinocr.italic_charmap[letter][0][a] > 0) 
              for a in range(8*13)]):
        # print "found character",letter
        return (letter,old_color), letter_start_x,letter_start_y
    return ('',None),-1,-1


  def match_with_character(self,x,y,origin=False,erase_color=(255,255,255,255)):
    '''
    with origin = true, (x,y) denotes the origin of where we expect
    the character to be; 
    with origin = false, (x,y) is the first 
    colored character found, and we must find the prospective origin
    to make the comparison
    '''
    old_color = None
    if origin == True:
      new_char = []
      for y1 in range(13):
        for x1 in range(8):
          try:
            if self.pix[x+x1,y+y1] in self.textcolors.keys():
              old_color = self.pix[x+x1,y+y1]
              c = 0
            else:
              c = 1
          except IndexError:
            return (' ',old_color), -1, -1
          new_char.append(c)
      # printmap(new_char)
      # print tuple(new_char)
      # print Dinocr.charmap[u'\xe8']
      if tuple(new_char) in Dinocr.revmap:
        self.erase_character_area(x,y,erase_color)
        return (Dinocr.revmap[tuple(new_char)],old_color),x,y
      else:
        return (' ',old_color),-1,-1
    
    # origin == False
    for letter in Dinocr.charmap.keys():
      offsetx,offsety = Dinocr.charmap[letter][1:]
      letter_start_x = x - offsetx
      letter_start_y = y-offsety
      if letter_start_x < 0 or letter_start_y < 0:
        continue
      # print("searching for exact match with %s at %d,%d" % 
      #       (letter,letter_start_x,letter_start_y))
      new_char = []
      for y1 in range(13):
        for x1 in range(8):
          try:
            if self.pix[letter_start_x+x1,letter_start_y+y1] in self.textcolors.keys():
              c = 0
            else:
              c = 1
            new_char.append(c)
          except IndexError:
            return ('',None),-1,-1
      # printmap(new_char)
      if all([(new_char[a] > 0) == 
              (Dinocr.charmap[letter][0][a] > 0) 
              for a in range(8*13)]):
        # print "found character",letter
        return (letter,old_color), letter_start_x,letter_start_y
    return ('',None),-1,-1

  def match_with_bold_character(self,x,y,origin=False,erase_color=(255,255,255,255)):
    '''
    with origin = true, (x,y) denotes the origin of where we expect
    the character to be; 
    with origin = false, (x,y) is the first 
    colored character found, and we must find the prospective origin
    to make the comparison
    '''
    old_color = None
    if origin == True:
      new_char = []
      for y1 in range(13):
        for x1 in range(9):
          try:

            if self.pix[x+x1,y+y1] in self.textcolors.keys():
              c = 0
              old_color = self.pix[x+x1,y+y1]
            else:
              c = 1
            new_char.append(c)
          except IndexError:
            return (' ',None),-1,-1
      if tuple(new_char) in Dinocr.bold_revmap:
        # print "found bold character",Dinocr.bold_revmap[tuple(new_char)],"at",str(x),str(y)
        self.erase_bold_character_area(x,y,erase_color)
        return (Dinocr.bold_revmap[tuple(new_char)],old_color),x,y
      else:
        # print_prospective_bold(self.pix,x,y)
        return (' ',None),-1,-1
    
    # origin == False
    for letter in Dinocr.bold_charmap.keys():
      offsetx,offsety = Dinocr.bold_charmap[letter][1:]
      letter_start_x = x - offsetx
      letter_start_y = y-offsety
      if letter_start_x < 0 or letter_start_y < 0:
        continue
      # print("searching for exact match with %s at %d,%d" % 
      #       (letter,letter_start_x,letter_start_y))
      new_char = []
      for y1 in range(13):
        for x1 in range(9):
          try:
            if self.pix[letter_start_x+x1,letter_start_y+y1] in self.textcolors.keys():
              old_color = self.pix[letter_start_x+x1,letter_start_y+y1] 
              c = 0
            else:
              c = 1
            new_char.append(c)
          except IndexError:
            return ('',None),-1,-1
      # printmap_bold(new_char)
      if all([(new_char[a] > 0) == 
              (Dinocr.bold_charmap[letter][0][a] > 0) 
              for a in range(9*13)]):
        # print "found character",letter
        return (letter,old_color), letter_start_x,letter_start_y
    return ('',None),-1,-1


  def find_aligned(self,originx,originy,bbox,color):
    line = []
    text_color = 'unknown'
    firstx = bbox[0] + ((originx - bbox[0]) % 8)
    left_edge = firstx
    last_x = bbox[2]
    last_y = bbox[3]
    firsty = originy
    while firsty < last_y - 13:
      text_this_line = False
      while firstx  < last_x - 8:
        this_character,temp_color = self.match_with_character(firstx,firsty,origin=True,erase_color=color)[0]
        if this_character == ' ':
          this_character,temp_color = self.match_with_italic_character(firstx,firsty,origin=True,erase_color=color)[0]
        if this_character != '' and this_character != ' ':
          text_color = temp_color
          text_this_line = True
        line.append(this_character)
        firstx += 8
      if text_this_line == False:
        return line,text_color
      line.append('\n')
      firsty += 13
      firstx = left_edge
    return line,text_color
 

  def find_aligned_bold(self,originx,originy,bbox,color):
    line = []
    text_color = 'unknown'
    firstx = bbox[0] + ((originx - bbox[0]) % 9)
    left_edge = firstx
    last_x = bbox[2]
    last_y = bbox[3]
    firsty = originy
    while firsty < last_y - 13:
      text_this_line = False
      while firstx  < last_x - 9:
        this_character,temp_color = self.match_with_bold_character(firstx,firsty,origin=True,erase_color=color)[0]
        # print "found %s at (%d,%d)" % (this_character,firstx,firsty)
        if this_character != '' and this_character != ' ':
          text_this_line = True
          text_color = temp_color
        line.append(this_character)
        firstx += 9
      if text_this_line == False:
        return line,text_color
      line.append('\n')
      firsty += 13
      firstx = left_edge
    return line,text_color
 

  def ocr_current_panel(self,bbox):
    d = DinosaurComicPanel()
    lines = []
    # increment the B in this color for each stanza to uniqueify them
    while True:
      startx,starty = self.find_first_pixel(bbox)
      # print "found new pixel at (%d,%d)" % (startx,starty)
      if startx < 0:
        break
      is_italic = False
      is_bold = False
      (letter,text_color), originx,originy = self.match_with_character(startx,starty)
      if letter == '':
        (letter,text_color), originx,originy = self.match_with_italic_character(startx,starty)
        if letter != '':
          is_italic = True
      if letter != '':
        # print "found normal/italic letter %s" % letter
        this_color = tuple(self.stanza_color)
        text,text_color = self.find_aligned(originx,originy,bbox,this_color)
        if len(''.join(text).strip()) == 0:
          letter = ''
        else:
          s = Stanza(text,text_color,this_color,is_bold=is_bold,is_italic=is_italic)
          self.stanza_colors[this_color] = s
          d.stanzas.append(s)
          self.stanza_color = (255,255,self.stanza_color[2] + 1,255)
          # self.comic_png.save('busted','PNG')
          continue
      (letter,text_color), originx,originy = self.match_with_bold_character(startx,starty)
      if letter != '':
        # print "found bold letter %s" % letter
        this_color = tuple(self.stanza_color)
        text,text_color = self.find_aligned_bold(originx,originy,bbox,this_color)
        if len(''.join(text).strip()) == 0:
          letter = ''
        else:
          s = Stanza(text,text_color,this_color,is_bold=True,is_italic=False)
          self.stanza_colors[this_color] = s
          d.stanzas.append(s)
          self.stanza_color = (255,255,self.stanza_color[2] + 1,255)
          continue
      if letter == '':
        # print "had to erase at",startx,starty
        retval = self.erase_contiguous(startx,starty)
        if retval:
          self.callouts.append(retval)
        continue
    return d

  @staticmethod
  def circle(x0,y0,radius):
    '''
    iterate over each pixel that is radius pixels away
    from x0,y0
    this value is used to find the nearest text/speaker to each
    end of a callout
    '''
    f = 1 - radius
    ddf_x = 1
    ddf_y = -2 * radius
    x = 0
    y = radius

    yield x0, y0 + radius
    yield x0, y0 - radius
    yield x0 + radius, y0
    yield x0 - radius, y0

    while x < y:
      if f >= 0: 
        y -= 1
        ddf_y += 2
        f += ddf_y
      x += 1
      ddf_x += 2
      f += ddf_x    
      yield x0 + x, y0 + y
      yield x0 - x, y0 + y
      yield x0 + x, y0 - y
      yield x0 - x, y0 - y
      yield x0 + y, y0 + x
      yield x0 - y, y0 + x
      yield x0 + y, y0 - x
      yield x0 - y, y0 - x



  def __init__(self,filename,url="unknown", title="unknown",mouseover_text='unknown',subject_text='unknown'):
    # filename can also be an fd
    self.uncertainty = 0
    self.panel_texts = []
    self.callouts = []
    self.imgname = filename
    self.erased_pixels = 0
    self.comic_text = DinosaurComic(filename)
    self.stanza_colors = {(255,255,100,255):Stanza('DINOCR ERROR TEXT',(0,0,0,255),(255,255,100,255))}
    self.url = url
    self.title = title
    self.mouseover_text = mouseover_text
    self.subject_text = subject_text
    self.new_xml = None
    self.old_xml = None
    
    cutpoints = []
    cutpoints.append((0,0,242,242))
    cutpoints.append((242,0,374,242))
    cutpoints.append((374,0,735,242))
    cutpoints.append((0,242,194,500))
    cutpoints.append((194,242,492,500))
    cutpoints.append((492,242,735,500))

    out = Image.new('1',(735,500),255)
    
    mask_png  = Image.open("dinocolors.png").convert('RGBA')
    comic_png = Image.open(filename).convert('RGBA')

    try:
      comic_png.paste(mask_png,mask_png)
      self.comic_png = comic_png
      self.pix = self.comic_png.load()
    except ValueError:
      return
    self.stanza_color = (255,255,0,255)
    for bbox in cutpoints:
      r = self.ocr_current_panel(bbox)
      self.comic_text.addpanel(r)

    # for stanza in self.comic_text.stanzas():
    #   print ''.join(stanza.words),stanza.color
    continuations = []
    for callout in self.callouts:
      talker,talkee = self.find_talkers(callout)
      if talker == 'continuation':
        continuations.append(talkee)
        continue
      if talker == (255,255,100,255):
        continue
      talker = Dinocr.colors[talker]
      talkee = self.stanza_colors[talkee]
      if talker == 'border':
        if talkee.is_bold:
          talker_color = Dinocr.textcolors[talkee.text_color]
          if talker_color == 'red':
            talker = 'The Devil'
          else:
            talker = 'God'
        else:
          talker = 'out of frame'
      talkee.speaker = talker
    progress = True
    numfixed = 0
    while progress:
      progress = False
      for c in continuations:
        c0 = self.stanza_colors[c[0]]
        c1 = self.stanza_colors[c[1]]
        if c0.speaker != 'unknown' and c1.speaker == 'unknown':
          progress = True
          numfixed += 1
          c1.speaker = c0.speaker
          # print "setting speaker for %s to %s"%(c1,c0)
          continue
        if c1.speaker != 'unknown' and c0.speaker == 'unknown':
          progress = True
          numfixed += 1
          c0.speaker = c1.speaker
          # print "setting speaker for %s to %s"%(c0,c1)
    if numfixed != len(continuations):
      # print "leftover continuation booo"
      self.uncertainty += 10

    for stanza in self.comic_text.stanzas():
      if stanza.speaker == 'unknown' and stanza.is_bold and stanza.text_color == (0,0,0,0xff):
        stanza.speaker = 'Narrator'
      if stanza.speaker == 'unknown':
        self.uncertainty += 100
    # print self.comic_text
    # self.comic_png.save('busted_2217.png','PNG')

  def find_talkers(self,callout):
    '''
    input: p1, p2
    intermediate value:
    foreach p:
      dino, dino_radius
      stanza, stanza_radius
      closest_thing = 'dino' if dr < sr else 'stanza'
    if p1.closest != p2.closest:
      dino on one side, stanza on other, match them up
    if p1.closest = dino:
      if dinos are same, return dino, min distance stanza
      if dinos are diff, return closest dino, opp side stanza
    if p1.closest = stanza:
      for now, set talker to "whoever said stanza #X" to bugtest
    '''
    cc = []
    talkpair = []
    for vertex in callout:
      c,r = self.find_closest_dinocolor(vertex)
      c1,r1 = self.find_closest_stanzacolor(vertex)
      if r < r1:
        closest = 'dino'
      else:
        closest = 'stanza'
      cc.append(
          {'dino':c,'dino_radius':r,'stanza':c1,'stanza_radius':r1,'closest':closest})
    if cc[0]['closest'] != cc[1]['closest']:
      if cc[0]['closest'] == 'dino':
        return cc[0]['dino'],cc[1]['stanza']
      else:
        return cc[1]['dino'],cc[0]['stanza']
    elif cc[0]['closest'] == 'dino':
      if cc[0]['dino'] == cc[1]['dino']:
        if cc[0]['stanza_radius'] < cc[1]['stanza_radius']:
          return cc[0]['dino'],cc[0]['stanza']
        else:
          return cc[1]['dino'],cc[1]['stanza']
      else:
        if cc[0]['dino_radius'] < cc[1]['dino_radius']:
          return cc[0]['dino'],cc[1]['stanza']
        else:
          return cc[1]['dino'],cc[0]['stanza']
    else: # closest to both ends is a stanza,
      if cc[0]['stanza'] == cc[1]['stanza']:
        # same stanza, return closest dino, that stanza
        if cc[0]['dino_radius'] < cc[1]['dino_radius']:
          return cc[0]['dino'],cc[0]['stanza']
        else:
          return cc[1]['dino'],cc[1]['stanza']
      else:
        # print "adding continuation: %s to %s" % (cc[0],cc[1])
        return 'continuation',(cc[0]['stanza'],cc[1]['stanza'])


  def find_closest_color(self,vertex,acceptable_colors=None):
    if acceptable_colors == None:
      acceptable_colors=(Dinocr.colors,self.stanza_colors)
    for radius in range(50):
      x,y = vertex
      for p in Dinocr.circle(x,y,radius):
        try:
          pixel_color = self.pix[p]
          # self.pix[p] = (0x88,0x88,0x88,0xff)
        except IndexError:
          # off canvas, ignore
          continue
        if any([pixel_color in x for x in acceptable_colors]):
          return pixel_color,radius
    # special error color
    return (255,255,100,255),500

  def find_closest_dinocolor(self,vertex):
    return self.find_closest_color(vertex,acceptable_colors=(Dinocr.colors,))

  def find_closest_stanzacolor(self,vertex):
    '''might never be used'''
    return self.find_closest_color(vertex,acceptable_colors=(self.stanza_colors,))

  def print_comic(self):
    print self.comic_text

  def store_comic_to_db(self,dbfile='comic.db'):
    '''writes comic to comic.db'''
    db = sqlite3.connect(dbfile)
    c = db.cursor()
    ''' TODO: create tables if file is empty'''
    c.execute("insert into comics values(NULL,'%s')" % self.imgname)
    c.execute("select last_insert_rowid()");
    comic_id = c.fetchone()[0]
    for panel_num in range(len(self.panel_texts)):
      this_panel = self.panel_texts[panel_num]
      for line_num in range(len(this_panel)):
        escaped_words = this_panel[line_num].replace("'","''")
        c.execute("insert into lines values(NULL,%d,%d,%d,'%s')" % (comic_id,panel_num+1,line_num+1,escaped_words))
    db.commit()

  def generate_old_xml(self):
    root = etree.Element('transcription')
    elt = etree.Element('url')
    elt.text = self.url
    root.append(elt)
    elt = etree.Element('title')
    elt.text = self.title
    root.append(elt)
    body = etree.Element('body')
    root.append(body)
    p = etree.Element('panel')
    body.append(p)
    for stanza in self.comic_text.stanzas():
      l = etree.Element('line')
      l.text = "%s: %s" % (stanza.speaker, stanza.text())
      p.append(l)
    self.old_xml = root

  def generate_new_xml(self):
    root = etree.Element('transcription')
    elt = etree.Element('url')
    elt.text = self.url
    root.append(elt)
    elt = etree.Element('title')
    elt.text = self.title
    root.append(elt)
    elt = etree.Element('subject')
    elt.text = self.subject_text
    root.append(elt)
    elt = etree.Element('mouseover')
    elt.text = self.mouseover_text
    root.append(elt)
    elt = etree.Element('uncertainty')
    elt.text = str(self.uncertainty)
    root.append(elt)
    body = etree.Element('body')
    root.append(body)
    for panel in self.comic_text.panels:
      p = etree.Element('panel')
      body.append(p)
      for stanza in panel.stanzas:
        l = etree.Element('line')
        l.text = "%s: %s" % (stanza.speaker, stanza.text())
        p.append(l)
    self.new_xml = root


  def string_old_xml(self):
    if not self.old_xml:
      self.generate_old_xml()
    return etree.tostring(self.old_xml, pretty_print=True)

  def string_new_xml(self):
    if not self.new_xml:
      self.generate_new_xml()
    return etree.tostring(self.new_xml, pretty_print=True)


    


  def choose_random_trigram(self):
    import random
    ''' return a trigram, trigramosaurus style'''
    comic_words = self.comic_text.text().split(' ')
    trigram_start = random.randint(0,len(comic_words)-3)
    trigram = ' '.join(comic_words[trigram_start:trigram_start+3])
    return trigram

if __name__ == '__main__':
  if len(sys.argv) > 1:
    filename = sys.argv[1]
  else:
    filename = "test_bold_italic.png"
  d = Dinocr(filename)
  d.print_comic()
  print "uncertainty:",d.uncertainty
  print d.string_new_xml()
  # d.store_comic_to_db()
  # print d.choose_random_trigram()
