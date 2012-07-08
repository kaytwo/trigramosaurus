import png
import sys
import pickle


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
 
class Dinocr:
  charmap_file = open('charmap.pkl','rb')
  charmap_bold = open('charmap_bold.pkl','rb')
  charmap_italic = open('charmap_italic.pkl','rb')

  italic_charmap = pickle.load(charmap_italic)
  italic_revmap = pickle.load(charmap_italic)

  bold_charmap = pickle.load(charmap_bold)
  bold_revmap = pickle.load(charmap_bold)

  charmap = pickle.load(charmap_file)
  revmap = pickle.load(charmap_file)

  italic_offset = [3,3,3,2,2,2,1,1,1,0,0,-1,-1]

  def __init__(self,image):
    
    r = png.Reader(bytes = image)
    self.sizex,self.sizey,self.pixels,dc = r.asDirect()
    self.pix = {}
    x = 0
    y = 0
    for row in self.pixels:
      x = 0
      for column in row:
        self.pix[x,y] = column
        x += 1
      y += 1
    

  def find_first_pixel(self,color=0):
    '''find the first black pixel scanning LR and TB'''
    this_line = []
    for y in range(self.sizey):
      for x in range(self.sizex):
        if self.pix[x,y] == color:
          # print("found top leftmost black pixel at %d,%d" % (x,y))
          return x,y
    return -1,-1

  def erase_contiguous(self,x,y):
    '''
    recursively blank every non-white pixel that is adjacent to this pixel
    very large colored blobs might exceed the recursion depth
    '''
    self.pix[x,y] = 1
    if self.pix[x-1,y] != 1:
      self.erase_contiguous(x-1,y)
    if self.pix[x+1,y] != 1:
      self.erase_contiguous(x+1,y)
    if self.pix[x,y-1] != 1:
      self.erase_contiguous(x,y-1)
    if self.pix[x,y+1] != 1:
      self.erase_contiguous(x,y+1)

  def erase_bold_character_area(self,x,y):
    '''blank the 9x13 area starting at (x,y)'''
    for y1 in range(13):
      for x1 in range(9):
        self.pix[x+x1,y+y1] = 1

  def erase_italic_character_area(self,x,y):
    '''blank the 8x13 area starting at (x,y)'''
    for y1 in range(13):
      for x1 in range(8):
        self.pix[x+x1 + Dinocr.italic_offset[y1],y+y1] = 1

  def erase_character_area(self,x,y):
    '''blank the 8x13 area starting at (x,y)'''
    for y1 in range(13):
      for x1 in range(8):
        self.pix[x+x1,y+y1] = 1

  def match_with_italic_character(self,x,y,origin=False):
    '''
    with origin = true, (x,y) denotes the origin of where we expect
    the character to be; 
    with origin = false, (x,y) is the first 
    colored character found, and we must find the prospective origin
    to make the comparison
    '''
    if origin == True:
      new_char = []
      for y1 in range(13):
        for x1 in range(8):
          try:
            new_char.append(self.pix[x + x1 + Dinocr.italic_offset[y1],
                                   y + y1])
          except KeyError:
            new_char.append(1)
      # print "testing aligned italic character:"
      # printmap(new_char)
      if tuple(new_char) in Dinocr.italic_revmap:
        self.erase_italic_character_area(x,y)
        return Dinocr.italic_revmap[tuple(new_char)],x,y
      else:
        return ' ',-1,-1
    
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
            new_char.append(self.pix[letter_start_x + x1 + Dinocr.italic_offset[y1],
                              letter_start_y + y1])
          except KeyError:
            new_char.append(1)

      # printmap(new_char)
      if all([(new_char[a] > 0) == 
              (Dinocr.italic_charmap[letter][0][a] > 0) 
              for a in range(8*13)]):
        # print "found character",letter
        return letter, letter_start_x,letter_start_y
    return '',-1,-1


  def match_with_character(self,x,y,origin=False):
    '''
    with origin = true, (x,y) denotes the origin of where we expect
    the character to be; 
    with origin = false, (x,y) is the first 
    colored character found, and we must find the prospective origin
    to make the comparison
    '''
    if origin == True:
      new_char = []
      for y1 in range(13):
        for x1 in range(8):
          new_char.append(self.pix[x + x1,
                                   y + y1])
      if tuple(new_char) in Dinocr.revmap:
        self.erase_character_area(x,y)
        return Dinocr.revmap[tuple(new_char)],x,y
      else:
        return ' ',-1,-1
    
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
          new_char.append(self.pix[letter_start_x + x1,
                              letter_start_y + y1])
      # printmap(new_char)
      if all([(new_char[a] > 0) == 
              (Dinocr.charmap[letter][0][a] > 0) 
              for a in range(8*13)]):
        # print "found character",letter
        return letter, letter_start_x,letter_start_y
    return '',-1,-1

  def match_with_bold_character(self,x,y,origin=False):
    '''
    with origin = true, (x,y) denotes the origin of where we expect
    the character to be; 
    with origin = false, (x,y) is the first 
    colored character found, and we must find the prospective origin
    to make the comparison
    '''
    if origin == True:
      new_char = []
      for y1 in range(13):
        for x1 in range(9):
          new_char.append(self.pix[x + x1,
                                   y + y1])
      if tuple(new_char) in Dinocr.bold_revmap:
        # print "found bold character",Dinocr.bold_revmap[tuple(new_char)],"at",str(x),str(y)
        self.erase_bold_character_area(x,y)
        return Dinocr.bold_revmap[tuple(new_char)],x,y
      else:
        # print_prospective_bold(self.pix,x,y)
        return ' ',-1,-1
    
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
          new_char.append(self.pix[letter_start_x + x1,
                              letter_start_y + y1])
      # printmap(new_char)
      if all([(new_char[a] > 0) == 
              (Dinocr.bold_charmap[letter][0][a] > 0) 
              for a in range(9*13)]):
        # print "found character",letter
        return letter, letter_start_x,letter_start_y
    return '',-1,-1


  def find_aligned(self,originx,originy):
    line = []
    firstx,firsty = originx % 8,originy
    while firsty < self.sizey - 13:
      text_this_line = False
      while firstx  < self.sizex - 8:
        this_character = self.match_with_character(firstx,firsty,origin=True)[0]
        if this_character == ' ':
          this_character = self.match_with_italic_character(firstx,firsty,origin=True)[0]
        if this_character != '' and this_character != ' ':
          text_this_line = True
        line.append(this_character)
        firstx += 8
      if text_this_line == False:
        return line
      line.append('\n')
      firsty += 13
      firstx = originx % 8
    return line
 

  def find_aligned_bold(self,originx,originy):
    line = []
    firstx,firsty = originx % 9,originy
    while firsty < self.sizey - 13:
      text_this_line = False
      while firstx  < self.sizex - 9:
        this_character = self.match_with_bold_character(firstx,firsty,origin=True)[0]
        if this_character != '' and this_character != ' ':
          text_this_line = True
        line.append(this_character)
        firstx += 9
      if text_this_line == False:
        return line
      line.append('\n')
      firsty += 13
      firstx = originx % 9
    return line
 

  def run(self):
    lines = []
    while True:
      startx,starty = self.find_first_pixel()
      if startx < 0:
        break
      letter, originx,originy = self.match_with_character(startx,starty)
      if letter == '':
        letter, originx,originy = self.match_with_italic_character(startx,starty)
        if letter != '' and letter != ' ':
          print "found italic letter",letter
      if letter != '':
        lines.append(self.find_aligned(originx,originy))
      letter, originx,originy = self.match_with_bold_character(startx,starty)
      if letter != '':
        lines.append(self.find_aligned_bold(originx,originy))
      if letter == '':
        # print "had to erase at",startx,starty
        self.erase_contiguous(startx,starty)
        continue

    return lines

if __name__ == '__main__':
  import Image, StringIO
  
  cutpoints = []
  cutpoints.append((0,0,242,242))
  cutpoints.append((242,0,374,242))
  cutpoints.append((374,0,735,242))
  cutpoints.append((0,242,194,500))
  cutpoints.append((194,242,492,500))
  cutpoints.append((492,242,735,500))

  out = Image.new('1',(735,500),255)
  im1 = Image.open("comic_mask.bmp")
  im2 = Image.open("test_italic.png")
  im1 = im1.convert('1')
  im2 = im2.convert('1')
  out.paste(im2,None,im1)
  panels = []
  panels.append(out.crop(cutpoints[4]))
  # for panel in cutpoints:
  #   panels.append(out.crop(panel))

  for offset in range(len(panels)):
    this_panel = panels[offset]
    f = StringIO.StringIO()
    this_panel.save(f,'png')
    lines = Dinocr(f.getvalue()).run()
    print "panel",offset+1,"text"
    for line in lines:
      print "someone said:"
      print ''.join(line).rstrip()
