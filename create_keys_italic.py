import Image,png
import sys

def create_charmap():
    keychars = r"""`~1234567890-=!@#$%^&*()_+qwertyuiop[]\QWERTYUIOP{}|asdfghjkl;'ASDFGHJKL:"zxcvbnm,./ZXCVBNM<>?"""
    keyimage = Image.open("italic.png")
    pix = keyimage.load()
    startx = 1
    starty = 0
    charnum = 0
    charmap = {}
    totalchars = len(keychars)
    y_offset = [3,3,3,2,2,2,1,1,1,0,0,-1,-1]


    while (starty <= 44):
      while (startx <= 565):
        charstring = []
        firstx = -1
        for y in range(0,13):
          for x in range(0,8):
            print "adding pixel at",startx + x + y_offset[y],starty + y
            charstring.append(pix[startx + x + y_offset[y],starty + y ])
            if firstx == -1 and pix[startx + x + y_offset[y],starty + y] == 0:
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
      startx = 1
charmap = create_charmap()
revmap = {}
for key in charmap.keys():
  charstring = charmap[key][0]
  revmap[tuple(charstring)] = key
charmap_output = open('charmap_italic.pkl','wb')
import pickle
pickle.dump(charmap,charmap_output)
pickle.dump(revmap,charmap_output)
charmap_output.close()

def printascii(s):
  for letter in s:
    big = charmap[letter]
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

