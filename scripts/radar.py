#!/usr/bin/env python3
"""
radar.py - render a spider / radar chart as a standalone SVG. Stdlib only.

Two sources of data:
  1. a JSON file you control
  2. live language stats from the GitHub API
"""
from __future__ import annotations
import argparse
import json
import math
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

THEMES = {
    "dark": {"grid":"#30363d","spoke":"#21262d","label":"#c9d1d9","value":"#8b949e","title":"#e6edf3","fill":"#39d353","stroke":"#3fb950","vertex":"#7ee787","bg":"none"},
    "light": {"grid":"#d0d7de","spoke":"#e6eaef","label":"#1f2328","value":"#57606a","title":"#1f2328","fill":"#2da44e","stroke":"#1a7f37","vertex":"#116329","bg":"none"},
}
UA = {"User-Agent":"radar.py"}

def esc(s: str) -> str:
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def from_json(path: Path):
    d=json.loads(path.read_text(encoding="utf-8"))
    axes=[(a["label"],float(a["value"])) for a in d["axes"]]
    return d.get("title","Skill Radar"), axes

def _api(url, token):
    req=urllib.request.Request(url, headers=dict(UA))
    if token: req.add_header("Authorization",f"Bearer {token}")
    with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode())

def from_github(user: str, token: str|None, limit: int, exclude: set[str], curve: float):
    totals={}; page=1
    while True:
        repos=_api(f"https://api.github.com/users/{user}/repos?per_page=100&page={page}&type=owner&sort=pushed",token)
        if not repos: break
        for repo in repos:
            if repo.get("fork") or repo.get("archived"): continue
            try: langs=_api(repo["languages_url"],token)
            except urllib.error.HTTPError: continue
            for name,count in langs.items():
                if name.lower() in exclude: continue
                totals[name]=totals.get(name,0)+count
        if len(repos)<100: break
        page+=1
    if not totals: sys.exit(f"no language data found for '{user}'")
    top=sorted(totals.items(),key=lambda kv:-kv[1])[:limit]
    # A language radar is useful for relative mix; sqrt compression avoids a single
    # dominant language pinning every other axis to the centre.
    peak=top[0][1]
    axes=[(n,round(100*(c/peak)**curve,1)) for n,c in top]
    return f"{user} · language mix", axes

def ring(radius,n,start=-math.pi/2):
    return [(radius*math.cos(start+i*2*math.pi/n), radius*math.sin(start+i*2*math.pi/n)) for i in range(n)]

def text_width(s,font_size): return len(s)*font_size*0.62


def render(title,axes,theme,size,rings,show_values,animate):
    c=THEMES[theme]; n=len(axes); r=size/2-8; gap=20
    vals=[max(0,min(100,v)) for _,v in axes]; outer=ring(r,n)
    labels=[]
    for i,(label,_) in enumerate(axes):
        ang=-math.pi/2+i*2*math.pi/n; cosv,sinv=math.cos(ang),math.sin(ang)
        lx,ly=(r+gap)*cosv,(r+gap)*sinv
        anchor="middle" if abs(cosv)<0.25 else ("start" if cosv>0 else "end")
        dy=4 if abs(sinv)<0.25 else (14 if sinv>0 else -5)
        labels.append((lx,ly+dy,anchor,label,vals[i]))
    minx,maxx,miny,maxy=-r,r,-r,r
    for lx,ly,anchor,label,v in labels:
        w=max(text_width(label,13),text_width(f"{v:g}",11) if show_values else 0)
        if anchor=="start": x0,x1=lx,lx+w
        elif anchor=="end": x0,x1=lx-w,lx
        else: x0,x1=lx-w/2,lx+w/2
        y0=ly-13; y1=ly+4+(15 if show_values else 0)
        minx,maxx=min(minx,x0),max(maxx,x1); miny,maxy=min(miny,y0),max(maxy,y1)
    pad=10; title_h=29 if title else 0
    W=round(maxx-minx+2*pad); H=round(maxy-miny+2*pad+title_h)
    ox,oy=-minx+pad,-miny+pad+title_h
    if title:
        need=round(text_width(title,15)+2*pad)
        if need>W: ox+=(need-W)/2; W=need
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(title) or "radar chart"}" font-family="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif">']
    if title: parts.append(f'<text x="{W/2:.1f}" y="25" text-anchor="middle" font-size="15" font-weight="700" fill="{c["title"]}">{esc(title)}</text>')
    parts.append(f'<g transform="translate({ox:.1f},{oy:.1f})">')
    for k in range(rings,0,-1):
        d=" ".join(f"{x:.1f},{y:.1f}" for x,y in ring(r*k/rings,n))
        parts.append(f'<polygon points="{d}" fill="none" stroke="{c["grid"]}" stroke-width="1" opacity="{0.35+0.5*k/rings:.2f}"/>')
    for x,y in outer: parts.append(f'<line x1="0" y1="0" x2="{x:.1f}" y2="{y:.1f}" stroke="{c["spoke"]}" stroke-width="1"/>')
    pts=" ".join(f"{outer[i][0]*vals[i]/100:.1f},{outer[i][1]*vals[i]/100:.1f}" for i in range(n))
    anim='<animateTransform attributeName="transform" type="scale" values="0.04;1" dur="1.1s" calcMode="spline" keyTimes="0;1" keySplines="0.22 1 0.36 1" fill="freeze"/>' if animate else ''
    parts.append(f'<g>{anim}<polygon points="{pts}" fill="{c["fill"]}" fill-opacity="0.22" stroke="{c["stroke"]}" stroke-width="2.5" stroke-linejoin="round"/>')
    for i in range(n):
        x,y=outer[i]; px=x*vals[i]/100; py=y*vals[i]/100
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.6" fill="{c["vertex"]}" stroke="{c["stroke"]}" stroke-width="1.2"/>')
    parts.append('</g>')
    for lx,ly,anchor,label,v in labels:
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-size="13" font-weight="600" fill="{c["label"]}">{esc(label)}</text>')
        if show_values: parts.append(f'<text x="{lx:.1f}" y="{ly+15:.1f}" text-anchor="{anchor}" font-size="11" fill="{c["value"]}">{v:g}</text>')
    parts.append('</g></svg>')
    return ''.join(parts)

def main(argv=None):
    p=argparse.ArgumentParser(); src=p.add_mutually_exclusive_group(required=True); src.add_argument('--data',type=Path); src.add_argument('--github')
    p.add_argument('-o','--out',type=Path,required=True); p.add_argument('--size',type=int,default=420); p.add_argument('--rings',type=int,default=4); p.add_argument('--limit',type=int,default=7); p.add_argument('--values',action='store_true'); p.add_argument('--curve',type=float,default=0.4); p.add_argument('--exclude',default=''); p.add_argument('--animate',action='store_true'); a=p.parse_args(argv)
    token=os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if a.data: title,axes=from_json(a.data)
    else: title,axes=from_github(a.github,token,a.limit,{x.strip().lower() for x in a.exclude.split(',') if x.strip()},a.curve)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    for theme in ('dark','light'):
        dest=a.out.parent/f'{a.out.name}-{theme}.svg'; dest.write_text(render(title,axes,theme,a.size,a.rings,a.values,a.animate),encoding='utf-8'); print(f'wrote {dest}')
if __name__=='__main__': main()
