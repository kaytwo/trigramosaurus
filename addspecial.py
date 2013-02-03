# vim: set fileencoding=utf-8

'''for adding extra letters'''

import pickle
import sys
from copy import deepcopy

charmap_file = open('charmap.pkl','rb')
charmap_bold = open('charmap_bold.pkl','rb')
charmap_italic = open('charmap_italic.pkl','rb')

italic_charmap = pickle.load(charmap_italic)
italic_revmap = pickle.load(charmap_italic)

bold_charmap = pickle.load(charmap_bold)
bold_revmap = pickle.load(charmap_bold)

charmap = pickle.load(charmap_file)
revmap = pickle.load(charmap_file)
charmap_file.close()


# print charmap
# print revmap

def printascii(s):
  for letter in s:
    big = charmap[letter][0]
    offset = 0
    for y in range(13):
      for x in range(8):
        if big[offset] == 1:
          sys.stdout.write(' ')
        else:
          sys.stdout.write('X')
        offset += 1
      print ""
    print ""

def printarray(s):
  for x in range(13):
    print charmap[s][0][x*8:(x+1)*8]

def add_acute_grave():
  printarray('d')
  gravee = list(deepcopy(charmap['e']))
  gravee[0][3] = 0
  gravee[0][4 + 8] = 0
  gravee[1] = 2
  gravee[2] = 0
  charmap[u'è'] = tuple(gravee)
  revmap[tuple(gravee[0])] = u'è'
  printascii(u'è')
  acutee = list(deepcopy(charmap['e']))
  acutee[0][4] = 0
  acutee[0][3 + 8] = 0
  acutee[1] = 3
  acutee[2] = 0
  charmap[u'é'] = tuple(acutee)

  revmap[tuple(acutee[0])] = u'é'

  charmapfile = open('charmap.pkl','wb')
  pickle.dump(charmap,charmapfile)
  pickle.dump(revmap,charmapfile)

def add_offset_comma():
  newcomma = list(deepcopy(charmap[',']))
  newcomma[0] = newcomma[0][1:]
  newcomma[0].append(1)
  print newcomma[0]
  revmap[tuple(newcomma[0])] = ','

  charmapfile = open('charmap.pkl','wb')
  pickle.dump(charmap,charmapfile)
  pickle.dump(revmap,charmapfile)

def add_offset_bold_comma():
  newcomma = list(deepcopy(bold_charmap[',']))
  newcomma[0] = newcomma[0][1:]
  newcomma[0].append(1)
  bold_revmap[tuple(newcomma[0])] = ','

  charmapfile = open('charmap_bold.pkl','wb')
  pickle.dump(bold_charmap,charmapfile)
  pickle.dump(bold_revmap,charmapfile)



if __name__=='__main__':
  pass
  # add_offset_bold_comma()

# print revmap
