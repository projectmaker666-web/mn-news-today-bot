import os,json,re,hashlib,time,calendar
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
 feeds_by_category=json.loads((ROOT/'config/feeds.json').read_text())
 feeds=feeds_by_category[CAT]
 
 print('Checking',len(feeds),'feeds; selected category:',CAT,flush=True)
 seen=set(json.loads((ROOT/'seen.json').read_text()) if (ROOT/'seen.json').exists() else [])
 for url in feeds:
  try:
   response=requests.get(url,timeout=15,headers={'User-Agent':'Mozilla/5.0 (compatible; MNNewsTodayBot/1.0)'})
   response.raise_for_status()
   data=feedparser.parse(response.content)
   print('Feed',urlparse(url).netloc,'status',response.status_code,'entries',len(data.entries),flush=True)
   for e in data.entries[:15]:
    link=e.get('link','');title=clean(e.get('title',''))
    if not link.startswith('https://') or len(title)<18 or hashlib.sha256(link.encode()).hexdigest() in seen:continue
    stamp=e.get('published_parsed') or e.get('updated_parsed')
    if not stamp:continue
    age=time.time()-calendar.timegm(stamp)
    if not 0<=age<=(7*24*3600 if DRY else 48*3600):continue
    return {'title':title,'summary':clean(e.get('summary',''))[:600],'link':link,'category':CAT}
  except Exception as ex:print('Feed skipped:',urlparse(url).netloc,type(ex).__name__,str(ex)[:140],flush=True)
 return None
def write(s):
 key=os.getenv('GEMINI_API_KEY')
 if not key:
  print('AI ERROR: GEMINI_API_KEY is missing',flush=True)
  return None
 try:
  from google import genai
  from google.genai import types
  prompt=('Та Монгол хэлээр Instagram мэдээ бэлтгэдэг редактор. '
   'ЗӨВХӨН өгөгдсөн эх сурвалжийн гарчиг, тайлбарт байгаа баримтыг ашигла. '
   'Баримт, тоо, ишлэл зохиож болохгүй. Гарчиг болон тайлбар нь МОНГОЛ хэлээр, '
   'кирилл үсгээр бичигдсэн байх ёстой. Эх сурвалжийн баримт дутуу бол '
   '{"headline":"","caption":""} гэж буцаа. JSON объект: headline, caption.\\n'
   +json.dumps(s,ensure_ascii=False))
  response=genai.Client(api_key=key).models.generate_content(
   model=os.getenv('GEMINI_MODEL','gemini-2.5-flash-lite'),
   contents=prompt,
   config=types.GenerateContentConfig(response_mime_type='application/json'))
  result=json.loads((response.text or '').strip())
  headline=result.get('headline','').strip()
  caption=result.get('caption','').strip()
  cyrillic=lambda t:len(re.findall(r'[А-Яа-яЁёӨөҮү]',t))
  if 8<=len(headline)<=110 and 20<=len(caption)<=1000 and cyrillic(headline)>=8 and cyrillic(caption)>=20:
   return headline,caption
  print('AI ERROR: missing/invalid Mongolian content; skipping',flush=True)
 except Exception as ex:
  print('AI ERROR:',type(ex).__name__,str(ex)[:350],flush=True)
 return None
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
 if not s:
  print('No eligible recent story; skip',flush=True)
  (OUT/'status.txt').write_text('No eligible article found. See feed diagnostics in the workflow logs.\n',encoding='utf-8')
  return
 result=write(s)
 if not result:
  print('AI declined article; skip',flush=True)
  (OUT/'status.txt').write_text('AI failed, returned non-Mongolian text, or article had insufficient facts.\n',encoding='utf-8')
  return
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
