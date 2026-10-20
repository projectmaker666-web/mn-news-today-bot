import os,json,re,hashlib,time
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import urlparse
import requests,feedparser
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).parent
OUT=ROOT/'public';OUT.mkdir(exist_ok=True)
DRY=os.getenv('DRY_RUN','true').lower()!='false'
CAT=['mongolia','geek','cinema'][datetime.now(timezone(timedelta(hours=8))).hour%3]
LABEL={'mongolia':'МОНГОЛ МЭДЭЭ','geek':'ТЕХНОЛОГИ • ТОГЛООМ','cinema':'КИНО ЕРТӨНЦ'}
TAGS={'mongolia':'#МонголМэдээ #MNNewsToday','geek':'#Gaming #Anime #Tech #MNNewsToday','cinema':'#Кино #Hollywood #MNNewsToday'}
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def clean(s):return re.sub(r'\s+',' ',re.sub(r'<[^>]*>',' ',str(s or ''))).strip()
def story():
 feeds=json.loads((ROOT/'config/feeds.json').read_text())[CAT]
 seen=set(json.loads((ROOT/'seen.json').read_text()) if (ROOT/'seen.json').exists() else [])
 for url in feeds:
  try:
   data=feedparser.parse(requests.get(url,timeout=15,headers={'User-Agent':'MNNewsBot/1.0'}).content)
   for e in data.entries[:15]:
    link=e.get('link','');title=clean(e.get('title',''))
    if not link.startswith('https://') or len(title)<18 or hashlib.sha256(link.encode()).hexdigest() in seen:continue
    stamp=e.get('published_parsed') or e.get('updated_parsed')
    if not stamp:continue
    age=time.time()-time.mktime(stamp)
    if not 0<=age<=48*3600:continue
    return {'title':title,'summary':clean(e.get('summary',''))[:600],'link':link}
  except Exception as ex:print('Feed skipped:',type(ex).__name__)
 return None
def write(s):
 key=os.getenv('GEMINI_API_KEY')
 if key:
  try:
   from google import genai
   prompt='Write a concise Mongolian Instagram news post using ONLY these RSS facts. Do not invent facts, numbers, or quotes. Return JSON with headline and caption. If facts insufficient output SKIP.\n'+json.dumps(s,ensure_ascii=False)
   answer=genai.Client(api_key=key).models.generate_content(model=os.getenv('GEMINI_MODEL','gemini-2.5-flash-lite'),contents=prompt).text.strip()
   if answer=='SKIP':return None
   result=json.loads(answer.removeprefix('```json').removesuffix('```').strip())
   if 8<=len(result['headline'])<=110 and 10<=len(result['caption'])<=600:return result['headline'],result['caption']
  except Exception as ex:print('AI unavailable:',type(ex).__name__)
 return s['title'][:100],'Эх сурвалжийн гарчиг: '+s['title'][:250]
def draw(title,source):
 img=Image.new('RGB',(1080,1350),'#111b2b');d=ImageDraw.Draw(img)
 d.rectangle((0,0,1080,20),fill='#ef4359')
 d.text((65,75),'MN NEWS TODAY',font=ImageFont.truetype(FONT,54),fill='#ffabb6')
 d.text((65,175),LABEL[CAT],font=ImageFont.truetype(FONT,36),fill='white')
 f=ImageFont.truetype(FONT,66);words=title.split();lines=[];line=''
 for w in words:
  test=(line+' '+w).strip()
  if d.textbbox((0,0),test,font=f)[2]<=950:line=test
  else:
   if line:lines.append(line)
   line=w
 if line:lines.append(line)
 for i,line in enumerate(lines[:8]):d.text((65,330+i*100),line,font=f,fill='white')
 d.rectangle((65,1160,1015,1166),fill='#ef4359')
 d.text((65,1210),'Эх сурвалж: '+source[:35],font=ImageFont.truetype(FONT,29),fill='#d3dce8')
 d.text((65,1270),'@mn_news_today',font=ImageFont.truetype(FONT,29),fill='#d3dce8')
 img.save(OUT/'latest.jpg',quality=92)
def main():
 s=story()
 if not s:print('No new recent story; skip');return
 result=write(s)
 if not result:print('Insufficient facts; skip');return
 headline,body=result
 caption=body+'\n\nЭх сурвалж: '+urlparse(s['link']).netloc+'\n'+s['link']+'\n\n'+TAGS[CAT]
 draw(headline,urlparse(s['link']).netloc)
 (OUT/'caption.txt').write_text(caption,encoding='utf-8')
 (OUT/'index.html').write_text('<h1>MN News Today</h1><img width="400" src="latest.jpg"><pre>'+__import__('html').escape(caption)+'</pre>',encoding='utf-8')
 print('PREVIEW:',CAT,s['link'],'DRY_RUN:',DRY)
 if not DRY:
  # Publication is intentionally blocked pending a separate, verified live publishing workflow.
  raise RuntimeError('Live publishing not enabled yet. Review dry-run preview first.')
if __name__=='__main__':main()
