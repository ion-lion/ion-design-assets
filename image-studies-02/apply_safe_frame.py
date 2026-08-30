#!/usr/bin/env python3
"""Inset every study's foreground into a crop-safe frame.

The full-canvas background stays fixed. All authored foreground is scaled to 80%
and centered, so no intentional overscan is mistaken for accidental clipping.
The chromatic study also replaces SVG paint-server strokes unsupported by the
pinned ImageMagick renderer with explicit reproducible colors.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

NS='http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
rootdir=Path(__file__).parent/'output'
palette=['#53f6d3','#bb5cff','#ff7849','#4fa8ff','#f8d44d']
for path in sorted(rootdir.glob('0[1-6]-*.svg')):
    tree=ET.parse(path); root=tree.getroot()
    if any((c.attrib.get('id')=='safe-frame') for c in root):
        continue
    children=list(root)
    base=None; defs=[]; foreground=[]
    for child in children:
        tag=child.tag.rsplit('}',1)[-1]
        if tag in ('title','desc'):
            continue
        if tag=='defs':
            defs.append(child); continue
        if base is None and tag=='rect' and child.attrib.get('width')=='2400' and child.attrib.get('height')=='1200' and not child.attrib.get('fill','').startswith('url('):
            base=child; continue
        # ImageMagick 6 renders these SVG gradient paint servers as black.
        if path.name.startswith('06-') and tag=='rect' and child.attrib.get('fill','').startswith('url('):
            continue
        foreground.append(child)
    for child in foreground:
        root.remove(child)
    group=ET.Element(f'{{{NS}}}g', {'id':'safe-frame','transform':'translate(240 120) scale(0.8)'})
    color_i=0
    for child in foreground:
        if path.name.startswith('06-'):
            for el in child.iter():
                for attr in ('stroke','fill'):
                    if el.attrib.get(attr,'').startswith('url('):
                        el.set(attr,palette[color_i % len(palette)])
                        color_i += 1
        group.append(child)
    root.append(group)
    tree.write(path, encoding='unicode', xml_declaration=False)
