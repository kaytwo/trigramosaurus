import Image,png
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
  charmap = pickle.load(charmap_file)
  revmap = pickle.load(charmap_file)

  def __init__(self,image_filename):
    f = open(image_filename,'rb')
    r = png.Reader(bytes = f.read())
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
    
    # print `dc`
    # sys.exit()

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
    '''recursively blank every non-white pixel that is adjacent to this pixel'''
    self.pix[x,y] = 1
    if self.pix[x-1,y] != 1:
      self.erase_contiguous(x-1,y)
    if self.pix[x+1,y] != 1:
      self.erase_contiguous(x+1,y)
    if self.pix[x,y-1] != 1:
      self.erase_contiguous(x,y-1)
    if self.pix[x,y+1] != 1:
      self.erase_contiguous(x,y+1)

  def erase_character_area(self,x,y):
    '''blank the 8x13 area starting at (x,y)'''
    for y1 in range(13):
      for x1 in range(8):
        self.pix[x+x1,y+y1] = 1

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
    self.erase_contiguous(x,y)
    return '',-1,-1


  def run(self):
    lines = []
    while True:
      startx,starty = self.find_first_pixel()
      if startx < 0:
        break
      letter, originx,originy = self.match_with_character(startx,starty)
      if letter == '':
        continue
      # found a text block: scan for anything that aligns with
      # this text
      lines.append([])
      firstx,firsty = originx % 8,originy
      while firsty < self.sizey - 13:
        while firstx  < self.sizex - 8:
          this_character = self.match_with_character(firstx,firsty,origin=True)[0]
          lines[-1].append(this_character)
          firstx += 8
        lines[-1].append('\n')
        firsty += 13
        firstx = originx % 8


      print  ''.join(lines[-1])
    sys.exit()

firstpanel = Dinocr('2.png')
firstpanel.run()
    
cutpoints = []
cutpoints.append((0,0,242,242))
cutpoints.append((242,0,374,242))
cutpoints.append((374,0,735,242))
cutpoints.append((0,242,194,500))
cutpoints.append((194,242,492,500))
cutpoints.append((492,242,735,500))

out = Image.new('1',(735,500),255)
im1 = Image.open("comic_mask.bmp")
im2 = Image.open("comic_test.png")
im1 = im1.convert('1')
im2 = im2.convert('1')
out.paste(im2,None,im1)
panels = []
for panel in cutpoints:
    panels.append(out.crop(panel))

for offset in range(len(panels)):
    panels[offset].save(str(offset)+'.png')

out.save('result.png')

