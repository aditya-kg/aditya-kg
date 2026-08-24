#!/usr/bin/env python3
"""Render GitHub profile stat and repository cards as local SVGs."""
from __future__ import annotations
import argparse, datetime as dt, json, os, urllib.error, urllib.request
from pathlib import Path
THEMES={"dark":{"bg":"#0d1117","border":"#30363d","title":"#39d353","text":"#c9d1d9","muted":"#8b949e","value":"#e6edf3"},"light":{"bg":"#ffffff","border":"#d0d7de","title":"#1a7f37","text":"#1f2328","muted":"#57606a","value":"#1f2328"}}
FONT="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif";UA={"User-Agent":"cards.py"}
LANG_COLOR={"JavaScript":"#f1e05a","TypeScript":"#3178c6","Python":"#3572A5","HTML":"#e34c26","CSS":"#563d7c","C++":"#f34b7d","C":"#555555","Java":"#b07219","Go":"#00ADD8","Rust":"#dea584","Shell":"#89e051","PLpgSQL":"#336790","Vue":"#41b883","Ruby":"#701516","PHP":"#4F5D95","Jupyter Notebook":"#DA5B0B","SCSS":"#c6538c","Svelte":"#ff3e00"}
ICON_STAR="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.75.75 0 01.719 4.192.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"
ICON_FORK="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75v-.878a2.25 2.25 0 111.5 0v.878a2.25 2.25 0 01-2.25 2.25h-1.5v2.128a2.251 2.251 0 11-1.5 0V8.5h-1.5A2.25 2.25 0 013.5 6.25v-.878a2.25 2.25 0 111.5 0z"
ICON_REPO="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9z"
def icon(path,x,y,size,fill):return f'<path transform="translate({x:.1f},{y:.1f}) scale({size/16:.3f})" fill="{fill}" d="{path}"/>'
def rest(path,token=None):
 req=urllib.request.Request("https://api.github.com"+path,headers=dict(UA))
 if token:req.add_header("Authorization",f"Bearer {token}")
 with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode())
def graphql(query,variables,token):
 body=json.dumps({"query":query,"variables":variables}).encode();req=urllib.request.Request("https://api.github.com/graphql",data=body,headers={**UA,"Content-Type":"application/json","Authorization":f"Bearer {token}"})
 with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode())
CONTRIB_QUERY='''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'''
def fetch_contributions(user,token):
 if not token:return None
 try:data=graphql(CONTRIB_QUERY,{"login":user},token)
 except urllib.error.HTTPError:return None
 if data.get("errors"):return None
 cal=data["data"]["user"]["contributionsCollection"]["contributionCalendar"];days=sorted((dt.date.fromisoformat(d["date"]),d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"])
 longest=run=0
 for _,c in days:run=run+1 if c>0 else 0;longest=max(longest,run)
 current=0
 for date,c in reversed(days):
  if c>0:current+=1
  elif date!=days[-1][0]:break
 return cal["totalContributions"],current,longest
def esc(s):return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
def text_width(s,size):return len(s)*size*.53
def wrap(text,size,max_w,max_lines):
 words=text.split();lines=[];cur=""
 for w in words:
  trial=f"{cur} {w}".strip()
  if text_width(trial,size)<=max_w or not cur:cur=trial
  else:lines.append(cur);cur=w
  if len(lines)==max_lines:break
 if cur and len(lines)<max_lines:lines.append(cur)
 return lines
def frame(w,h,c,body,label):return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}" font-family="{FONT}"><rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>{body}</svg>'
def render_stats(user,stats,theme):
 c=THEMES[theme];pad=22;cols=4;W=480;tw=(W-2*pad)/cols;rh=48;rows=(len(stats)+cols-1)//cols;H=pad+52+(rows-1)*rh+17+pad
 out=[f'<text x="{pad}" y="{pad+14}" font-size="15" font-weight="700" fill="{c["title"]}">{esc(user)}</text>',f'<text x="{W-pad}" y="{pad+14}" font-size="11" text-anchor="end" fill="{c["muted"]}">at a glance</text>',f'<line x1="{pad}" y1="{pad+26}" x2="{W-pad}" y2="{pad+26}" stroke="{c["border"]}"/>']
 top=pad+52
 for i,(value,label) in enumerate(stats):
  cx=pad+(i%cols)*tw;cy=top+(i//cols)*rh
  out += [f'<text x="{cx:.0f}" y="{cy:.0f}" font-size="23" font-weight="700" fill="{c["value"]}">{esc(value)}</text>',f'<text x="{cx:.0f}" y="{cy+17:.0f}" font-size="10.5" fill="{c["muted"]}">{esc(label)}</text>']
 return frame(W,H,c,"".join(out),f"{user} GitHub statistics")
def render_repo(repo,theme):
 c=THEMES[theme];W,H=420,132;pad=18;out=[icon(ICON_REPO,pad,pad,15,c["muted"]),f'<text x="{pad+22}" y="{pad+12}" font-size="14.5" font-weight="700" fill="{c["title"]}">{esc(repo["name"])}</text>']
 for i,line in enumerate(wrap(repo.get("description") or "No description yet.",11.5,W-2*pad,3)):out.append(f'<text x="{pad}" y="{pad+36+i*16}" font-size="11.5" fill="{c["text"]}">{esc(line)}</text>')
 fy=H-pad-2;x=pad
 if repo.get("language"):
  col=LANG_COLOR.get(repo["language"],c["muted"]);out += [f'<circle cx="{x+5}" cy="{fy-4}" r="5" fill="{col}"/>',f'<text x="{x+15}" y="{fy}" font-size="11" fill="{c["muted"]}">{esc(repo["language"])}</text>'];x+=15+text_width(repo["language"],11)+18
 for path,count in ((ICON_STAR,repo.get("stars",0)),(ICON_FORK,repo.get("forks",0))):
  out += [icon(path,x,fy-11,12,c["muted"]),f'<text x="{x+17}" y="{fy}" font-size="11" fill="{c["muted"]}">{count}</text>'];x+=17+text_width(str(count),11)+18
 return frame(W,H,c,"".join(out),f'{repo["name"]} repository card')
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--user",required=True);p.add_argument("--out",type=Path,default=Path("assets"));p.add_argument("--projects",type=Path,default=Path("assets/projects.json"));a=p.parse_args(argv)
 token=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN");a.out.mkdir(parents=True,exist_ok=True);user=rest(f"/users/{a.user}",token);repos=[];page=1
 while True:
  batch=rest(f"/users/{a.user}/repos?per_page=100&page={page}&type=owner",token);repos+=batch
  if len(batch)<100:break
  page+=1
 contrib=fetch_contributions(a.user,token);total=contrib[0] if contrib else "—";longest=contrib[2] if contrib else "—"
 tiles=[(f"{user['public_repos']:,}","Public repos"),(f"{user['followers']:,}","Followers"),(f"{total:,}" if isinstance(total,int) else total,"Contributions (1y)"),(f"{longest:,}" if isinstance(longest,int) else longest,"Longest streak")]
 for theme in ("dark","light"):(a.out/f"card-stats-{theme}.svg").write_text(render_stats(a.user,tiles,theme),encoding="utf-8")
 if not a.projects.exists():return
 wanted=json.loads(a.projects.read_text(encoding="utf-8"))["projects"];by_name={r["name"].lower():r for r in repos}
 for entry in wanted:
  src=by_name.get(entry["repo"].lower())
  if not src:continue
  card={"name":src["name"],"description":entry.get("description") or src.get("description"),"language":entry.get("language") or src.get("language"),"stars":src["stargazers_count"],"forks":src["forks_count"]}
  for theme in ("dark","light"):(a.out/f"card-{src['name']}-{theme}.svg").write_text(render_repo(card,theme),encoding="utf-8")
if __name__=='__main__':main()
