#!/usr/bin/env python3
"""Fail the build for likely crop, grayscale, dimension, or artifact errors."""
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).parent
OUT=ROOT/'output'
EXPECTED=(1200,600)
CHROMA_MIN=0.02
EDGE_STD_MAX=0.002

def run(*args):
    return subprocess.check_output(args,text=True).strip()

def fx(path, expression, *ops):
    return float(run('convert',str(path),*ops,'-format',f'%[fx:{expression}]','info:'))

def channel_diff(path,a,b):
    pa=Path('/tmp')/f'ion-{a}.png'; pb=Path('/tmp')/f'ion-{b}.png'
    subprocess.check_call(['convert',str(path),'-colorspace','sRGB','-channel',a,'-separate',str(pa)])
    subprocess.check_call(['convert',str(path),'-colorspace','sRGB','-channel',b,'-separate',str(pb)])
    return float(run('convert',str(pa),str(pb),'-compose','difference','-composite','-format','%[fx:mean]','info:'))

def edge_std(path,w,h,n=12):
    crops=[f'{w}x{n}+0+0',f'{w}x{n}+0+{h-n}',f'{n}x{h}+0+0',f'{n}x{h}+{w-n}+0']
    
    values=[]
    for i,c in enumerate(crops):
        crop=Path('/tmp')/f'ion-edge-{i}.png'
        subprocess.check_call(['convert',str(path),'-crop',c,'+repage',str(crop)])
        for channel in ('R','G','B'):
            values.append(float(run('convert',str(crop),'-channel',channel,'-separate','-format','%[fx:standard_deviation]','info:')))
    return max(values)

results=[]; failures=[]
for p in sorted(OUT.glob('0[1-6]-*.png')):
    dims=run('identify','-format','%w %h',str(p)).split(); w,h=map(int,dims)
    rg=channel_diff(p,'R','G'); gb=channel_diff(p,'G','B')
    edge=edge_std(p,w,h)
    item={'file':p.name,'width':w,'height':h,'rg_difference':round(rg,6),'gb_difference':round(gb,6),'max_edge_stddev':round(edge,6)}
    results.append(item)
    if (w,h)!=EXPECTED: failures.append(f'{p.name}: expected {EXPECTED}, got {(w,h)}')
    if edge>EDGE_STD_MAX: failures.append(f'{p.name}: edge variation {edge:.6f} suggests clipped foreground')
    if p.name.startswith('06-') and max(rg,gb)<CHROMA_MIN: failures.append(f'{p.name}: chroma {max(rg,gb):.6f} below {CHROMA_MIN}')
report={'checks':{'dimensions':EXPECTED,'max_edge_stddev':EDGE_STD_MAX,'chromatic_min_channel_difference':CHROMA_MIN},'artifacts':results,'failures':failures}
(OUT/'review-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if failures: sys.exit(1)
