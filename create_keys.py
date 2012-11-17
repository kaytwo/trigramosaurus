import Image,png
import sys

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
        firstx = -1
        for y in range(0,13):
          for x in range(0,8):
            if pix[startx+x,starty+y][0] > 0:
              thispixel = 1
            else:
              thispixel = 0
            charstring.append(thispixel)
            if firstx == -1 and thispixel == 0:
              firstx = x
              firsty = y
        if all(charstring):
          break
        charmap[keychars[charnum]] = charstring,firstx,firsty
        charnum = charnum + 1
        if charnum == totalchars:
          return charmap
        startx = startx + 16
      starty = starty + 14
      startx = 0
charmap = create_charmap()
revmap = {}
for key in charmap.keys():
  charstring = charmap[key][0]
  revmap[tuple(charstring)] = key
charmap_output = open('charmap.pkl','wb')
import pickle
pickle.dump(charmap,charmap_output)
pickle.dump(revmap,charmap_output)
charmap_output.close()
sys.exit()

def printascii(s):
  for letter in s:
    big = charmap[letter]
    offset = 0
    for y in range(13):
      for x in range(8):
        if big[offset][0] == 1:
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

