import Image,png

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

