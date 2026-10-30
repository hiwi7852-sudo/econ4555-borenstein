"""Download official month-filtered T-100 extracts with a 250 MiB streaming limit."""
import urllib.request,urllib.parse,http.cookiejar,re,html,json,hashlib,sys
from pathlib import Path
from fetch_bts import validate_archive
from datetime import datetime,timezone
base='https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=GEE&QO_fu146_anzr=Nv4%20Pn44vr45'
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
fields=['DEPARTURES_SCHEDULED','DEPARTURES_PERFORMED','SEATS','PASSENGERS','DISTANCE','UNIQUE_CARRIER','AIRLINE_ID','UNIQUE_CARRIER_NAME','ORIGIN_AIRPORT_ID','ORIGIN','DEST_AIRPORT_ID','DEST','AIRCRAFT_TYPE','AIRCRAFT_CONFIG','YEAR','QUARTER','MONTH','CLASS']
root=Path(__file__).resolve().parents[1]/'data/raw/2025Q2'
root.mkdir(parents=True,exist_ok=True)
for month in [4,5,6]:
 p=root/f'T100_Domestic_Segment_2025_{month:02}.zip'
 if p.exists():
  print('Exists; refusing overwrite:',p);continue
 try:
  with op.open(base,timeout=60) as r:s=r.read().decode()
  data={}
  for tag in re.findall(r'<input\b[^>]*>',s,re.I):
   attrs=dict((k.lower(),html.unescape(v)) for k,v in re.findall(r'(\w+)="([^"]*)"',tag))
   if attrs.get('type')=='hidden':data[attrs['name']]=attrs.get('value','')
  data.update(cboGeography='All',cboYear='2025',cboPeriod=str(month),btnDownload='Download')
  data.update({x:'on' for x in fields})
  req=urllib.request.Request(base,data=urllib.parse.urlencode(data).encode())
  p=root/f'T100_Domestic_Segment_2025_{month:02}.zip';tmp=p.with_suffix('.part');h=hashlib.sha256();n=0
  with op.open(req,timeout=120) as r,open(tmp,'wb') as out:
   print(month,r.status,r.url,r.headers.get('Content-Type'),r.headers.get('Content-Length'),flush=True)
   if int(r.headers.get('Content-Length','0'))>250*1024**2:raise ValueError('Compressed size limit exceeded')
   while b:=r.read(1024*1024):
    n+=len(b)
    if n>250*1024**2:raise ValueError('Transfer limit exceeded')
    out.write(b);h.update(b)
   final=r.url
  with open(tmp,'rb') as check: signature=check.read(2)
  if signature!=b'PK':
   tmp.unlink();raise ValueError('HTTP response was not a ZIP archive')
  members=validate_archive(tmp);tmp.rename(p)
  p.with_suffix('.zip.json').write_text(json.dumps(dict(source_url=base,final_url=final,post_parameters={k:v for k,v in data.items() if not k.startswith('__')},retrieved_utc=datetime.now(timezone.utc).isoformat(),bytes=n,sha256=h.hexdigest(),members=members,period_verified=False),indent=2))
  print('SUCCESS',month,n,members,flush=True)
 except Exception as e:
  print('ERROR',month,type(e).__name__,str(e),flush=True)
  if 'tmp' in locals():tmp.unlink(missing_ok=True)
  raise
