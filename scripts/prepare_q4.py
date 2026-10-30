"""Chunked official ZIP ingestion and auditable Q4 variable construction. See docs/question-4.md."""
import argparse,json,zipfile,hashlib
from pathlib import Path
import pandas as pd
import duckdb
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/2025Q2'
WORK=ROOT/'work'
WORK.mkdir(exist_ok=True)
con=duckdb.connect(str(WORK/'q4.duckdb'))
con.execute("SET memory_limit='2GB'; SET threads=2")
con.execute(f"SET temp_directory='{WORK}/duckdb-temp'")

def ingest():
 specs={'market':['ItinID','MktID','MktCoupons','Year','Quarter','OriginAirportID','Origin','OriginCountry','DestAirportID','Dest','DestCountry','TkCarrierChange','OpCarrierChange','RPCarrier','TkCarrier','OpCarrier','BulkFare','Passengers','MktFare','MktDistance','MktMilesFlown','NonStopMiles','ItinGeoType','MktGeoType'],
 'ticket':['ItinID','Coupons','Year','Quarter','OriginAirportID','Origin','OriginCountry','RoundTrip','OnLine','DollarCred','RPCarrier','Passengers','ItinFare','BulkFare','ItinGeoType'],
 'coupon':None,'t100':None}
 report={}
 for table,cols in specs.items():
  pattern={'market':'*DB1BMarket*.zip','ticket':'*DB1BTicket*.zip','coupon':'*DB1BCoupon*.zip','t100':'T100*.zip'}[table]
  files=sorted(RAW.glob(pattern))
  if not files:raise FileNotFoundError(pattern)
  con.execute(f'DROP TABLE IF EXISTS {table}')
  first=True
  for p in files:
   with zipfile.ZipFile(p) as z:
    name=next(n for n in z.namelist() if n.lower().endswith('.csv'))
    for chunk in pd.read_csv(z.open(name),usecols=cols,chunksize=100000,low_memory=False,keep_default_na=False):
     chunk=chunk.loc[:,~chunk.columns.str.startswith('Unnamed')]
     # Infer numeric columns consistently; carrier codes such as NA remain literal.
     for c in chunk:
      if c.lower() in ['itinid','mktid']:chunk[c]=pd.to_numeric(chunk[c],errors='raise').astype('int64')
     con.register('chunk',chunk)
     if first:con.execute(f'CREATE TABLE {table} AS SELECT * FROM chunk');first=False
     else:con.execute(f'INSERT INTO {table} BY NAME SELECT * FROM chunk')
   print('Ingested',p.name,flush=True)
  report[table]={'rows':con.execute(f'SELECT count(*) FROM {table}').fetchone()[0], 'schema':con.execute(f'DESCRIBE {table}').fetchall(), 'periods':con.execute(f'SELECT Year,Quarter,count(*) FROM {table} GROUP BY ALL').fetchall()}
  assert con.execute(f'SELECT count(*) FROM {table} WHERE Year<>2025 OR Quarter<>2').fetchone()[0]==0
  if table!='t100':
   keys={'market':'Year,Quarter,ItinID,MktID','ticket':'Year,Quarter,ItinID','coupon':'Year,Quarter,ItinID,SeqNum'}[table]
   report[table]['duplicate_keys']=con.execute(f'SELECT count(*) FROM (SELECT {keys},count(*) n FROM {table} GROUP BY ALL HAVING n>1)').fetchone()[0]
  else:report[table]['months']=con.execute('SELECT Month,count(*) FROM t100 GROUP BY ALL ORDER BY Month').fetchall()
 (WORK/'validation-ingest.json').write_text(json.dumps(report,indent=2,default=str))
 print(json.dumps({k:{a:b for a,b in v.items() if a!='schema'} for k,v in report.items()},indent=2),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--ingest',action='store_true');a=parser.parse_args()
 if a.ingest:ingest()
