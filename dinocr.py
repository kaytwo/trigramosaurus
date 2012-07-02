import Image,png
import sys
import pickle


def printmap(s):
    offset = 0
    for y in range(12):
      for x in range(8):
        if s[offset] >= 1:
          sys.stdout.write(' ')
        else:
          sys.stdout.write('X')
        offset += 1
      print ""



def printascii(s):
  for letter in s:
    big = charmap[letter]
    offset = 0
    for y in range(12):
      for x in range(8):
        if big[offset][0] == 1:
          sys.stdout.write(' ')
        else:
          sys.stdout.write('X')
        offset += 1
      print ""
    print ""

def print_prospective(pix):
  for y in range(12):
    for x in range(8):
      if pix[x,y] > 0:
        sys.stdout.write(' ')
      else:
        sys.stdout.write('X')
    print ""
  

charmap_file = open('charmap.pkl','rb')
charmap = pickle.load(charmap_file)

testimage = Image.open('0.png')
sizex,sizey = testimage.size
pix = testimage.load()
# find the top leftmost black pixel
this_line = []
for y in range(sizey):
  for x in range(sizex):
    if pix[x,y] != 0:
      continue
    print("found top leftmost black pixel at %d,%d" % (x,y))
    for letter in charmap.keys():
      offsetx,offsety = charmap[letter][1:]
      letter_start_x = x - offsetx
      letter_start_y = y-offsety
      if letter_start_x < 0 or letter_start_y < 0:
        continue
      print("searching for exact match with %s at %d,%d" % 
            (letter,letter_start_x,letter_start_y))
      new_char = []
      for y1 in range(12):
        for x1 in range(8):
          new_char.append(pix[letter_start_x + x1,
                              letter_start_y + y1])
      printmap(new_char)
      if all([(new_char[a] > 0) == (charmap[letter][0][a] > 0) for a in range(8*12)]):
        print "found character",letter
        this_line.append(letter)

    sys.exit()

# for each letter in the charmap:

# crop to the box relative to first pixel in the prospective letter

# test for equality, if so, print origin coord and letter

sys.exit()

def create_charmap():
    keychars = r"""`~1234567890-=!@#$%^&*()_+qwertyuiop[]\QWERTYUIOP{}|asdfghjkl;'ASDFGHJKL:"zxcvbnm,./ZXCVBNM<>?"""
    keyimage = Image.open("normal.png")
    pix = keyimage.load()
    startx = 0
    starty = 0
    charnum = 0
    charmap = {}
    totalchars = len(keychars)


    while (starty <= 44):
      while (startx <= 561):
        charstring = []
        for y in range(0,12):
          for x in range(0,8):
            charstring.append(pix[startx + x,starty + y])
        if all(charstring):
          break
        charmap[keychars[charnum]] = charstring
        charnum = charnum + 1
        if charnum == totalchars:
          return charmap
        startx = startx + 16
      starty = starty + 14
      startx = 0
charmap = create_charmap()
charmap_output = open('charmap.pkl','wb')
import pickle
pickle.dump(charmap,charmap_output)
charmap_output.close()
sys.exit()

def printascii(s):
  for letter in s:
    big = charmap[letter]
    offset = 0
    for y in range(12):
      for x in range(8):
        if big[offset] == 1:
          sys.stdout.write(' ')
        else:
          sys.stdout.write('X')
        offset += 1
      print ""
    print ""

printascii('chris')

sys.exit()

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

