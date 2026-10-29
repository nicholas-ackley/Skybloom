import sys, json
from PIL import Image
import numpy as np
from scipy import ndimage
S=2.56
import os
OUT=sys.argv[3]; os.makedirs(OUT,exist_ok=True)
src=sys.argv[1]
im=np.asarray(Image.open(src).convert('RGB')).astype(float)
H,W,_=im.shape
bg=np.array([188,200,194.])
d=np.abs(im-bg).sum(2)
mask=ndimage.binary_dilation(d>25,iterations=3)
lab,n=ndimage.label(mask)
blocks=[]
for k,sl in enumerate(ndimage.find_objects(lab)):
    y0,y1=sl[0].start,sl[0].stop; x0,x1=sl[1].start,sl[1].stop
    if (d[sl]>25).sum()<60: continue
    best=None
    for py in np.arange(0,S,0.16):
        for px in np.arange(0,S,0.16):
            nx=int((x1-x0-px)/S); ny=int((y1-y0-py)/S)
            xs=(x0+px+(np.arange(nx)+0.5)*S).astype(int); ys=(y0+py+(np.arange(ny)+0.5)*S).astype(int)
            smp=im[np.ix_(ys,xs)]
            sc=np.abs(np.diff(smp,axis=0)).sum()+np.abs(np.diff(smp,axis=1)).sum()
            sc/= (nx*ny)
            if best is None or sc>best[0]: best=(sc,px,py,smp)
    _,px,py,smp=best
    dd=np.abs(smp-bg).sum(2)
    alpha=dd>int(sys.argv[2])
    ys,xs=np.nonzero(alpha)
    smp=smp[ys.min():ys.max()+1, xs.min():xs.max()+1]; alpha=alpha[ys.min():ys.max()+1, xs.min():xs.max()+1]
    ax=(x0+px)/S+xs.min(); ay=(y0+py)/S+ys.min()
    rgba=np.dstack([smp,alpha*255]).astype(np.uint8)
    blocks.append(dict(x=round(ax,1),y=round(ay,1),w=rgba.shape[1],h=rgba.shape[0]))
    Image.fromarray(rgba,'RGBA').save(f'{OUT}/b{len(blocks)-1:03d}.png')
json.dump(blocks,open(OUT+'/index.json','w'),indent=0)
for i,b in enumerate(blocks): print(i,b, (b['w']%16,b['h']%16))
