"""Modern Table 1: full validated fare records, declared airport rule, and parent groupings.
Run after prepare_q4.py and build_q4.py. Does not estimate regressions.
"""
from pathlib import Path
import json,hashlib
import duckdb
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/part3-q5';OUT.mkdir(parents=True,exist_ok=True)
con=duckdb.connect(str(ROOT/'work/q4.duckdb'),read_only=True)
con.execute("SET memory_limit='2GB'; SET threads=2")
con.execute(f"SET temp_directory='{ROOT}/work/q5-spill'")
# Parent ownership as of 2025 Q2; historical predecessor codes have disappeared.
def parent(col):return f"CASE WHEN {col} IN ('AS','HA') THEN 'AS_HA' ELSE {col} END"
valid="NOT IN ('','99','--')"
con.execute(f'''CREATE TEMP TABLE origins AS WITH n AS (
 SELECT OriginAirportID airport,Origin airport_code,{parent('first_carrier')} parent,sum(Passengers) passengers
 FROM ticket_orig WHERE Passengers>0 AND ItinGeoType IN (1,2) AND OriginCountry='US' AND DollarCred=1 AND BulkFare=0 AND first_carrier {valid} GROUP BY ALL)
 SELECT *,passengers/sum(passengers) OVER(PARTITION BY airport) origin_share FROM n''')
con.execute(f'''CREATE TEMP TABLE boardings AS WITH n AS (
 SELECT c.OriginAirportID airport,{parent('c.TkCarrier')} parent,sum(c.Passengers) passengers
 FROM coupon c JOIN ticket t USING(Year,Quarter,ItinID)
 WHERE c.Passengers>0 AND c.ItinGeoType IN (1,2) AND c.OriginCountry='US' AND c.DestCountry='US' AND c.CouponType='A'
 AND t.DollarCred=1 AND t.BulkFare=0 AND c.TkCarrier {valid} GROUP BY ALL)
 SELECT *,passengers/sum(passengers) OVER(PARTITION BY airport) coupon_boarding_share FROM n''')
con.execute('''CREATE TEMP TABLE traffic AS SELECT Origin_Airport_ID airport,Origin airport_code,sum(Passengers) actual_segment_boardings
 FROM t100 WHERE Year=2025 AND Quarter=2 AND Class IN ('A','C','E','F') AND Seats>0 AND Departures_Performed>0 AND Passengers>=0 GROUP BY ALL''')
con.execute('''CREATE TEMP TABLE selection_universe AS SELECT o.*,t.actual_segment_boardings,b.coupon_boarding_share
 FROM origins o JOIN traffic t USING(airport) LEFT JOIN boardings b USING(airport,parent)''')
con.execute('''CREATE TEMP TABLE selected AS SELECT *,row_number() OVER(ORDER BY origin_share DESC,actual_segment_boardings DESC,airport_code,parent) display_order
 FROM selection_universe WHERE actual_segment_boardings>=2500000 AND origin_share>=0.5
 QUALIFY display_order<=6''')
assert con.execute('SELECT count(*) FROM selected').fetchone()[0]==6
con.execute('''CREATE TEMP TABLE historical AS SELECT *,row_number() OVER(ORDER BY CASE airport_code WHEN 'STL' THEN 1 WHEN 'MSP' THEN 2 WHEN 'PIT' THEN 3 WHEN 'DFW' THEN 4 WHEN 'ORD' THEN 5 WHEN 'ATL' THEN 6 END) display_order FROM (
 SELECT *,row_number() OVER(PARTITION BY airport ORDER BY origin_share DESC,parent) carrier_rank FROM selection_universe
 WHERE airport_code IN ('STL','MSP','PIT','DFW','ORD','ATL')) WHERE carrier_rank=1''')
con.execute('''CREATE TEMP TABLE pairs AS SELECT 'A' panel,airport,airport_code,parent,origin_share,coupon_boarding_share,actual_segment_boardings,display_order FROM selected
 UNION ALL SELECT 'B',airport,airport_code,parent,origin_share,coupon_boarding_share,actual_segment_boardings,display_order FROM historical''')
con.execute(f'''CREATE TEMP TABLE fare_sample AS SELECT *,{parent('carrier')} parent,
 CASE WHEN NonStopMiles<200 THEN 0 WHEN NonStopMiles<500 THEN 1 WHEN NonStopMiles<1000 THEN 2 WHEN NonStopMiles<1500 THEN 3 WHEN NonStopMiles<2000 THEN 4 ELSE 5 END bin FROM clean WHERE carrier {valid}''')
con.execute('''CREATE TEMP TABLE benchmark AS SELECT coalesce(bin,6) bin,count(*) records,sum(Passengers) sampled_passengers,
 sum(Passengers*MktFare) sampled_revenue,sum(Passengers*NonStopMiles) sampled_od_miles,
 100*sum(Passengers*MktFare)/sum(Passengers*NonStopMiles) yield_cents FROM fare_sample GROUP BY GROUPING SETS ((bin),())''')
con.execute('''CREATE TEMP TABLE comparisons AS WITH x AS (
 SELECT p.panel,p.display_order,p.airport,p.airport_code,p.parent,f.bin,f.Passengers,f.MktFare,f.NonStopMiles,
 CASE WHEN p.parent=f.parent AND p.airport NOT IN (f.OriginAirportID,f.DestAirportID) THEN 0
 WHEN p.parent=f.parent AND p.airport IN (f.OriginAirportID,f.DestAirportID) THEN 1
 WHEN p.parent<>f.parent AND p.airport IN (f.OriginAirportID,f.DestAirportID) THEN 2 END category
 FROM pairs p JOIN fare_sample f ON p.parent=f.parent OR p.airport IN (f.OriginAirportID,f.DestAirportID))
 SELECT panel,display_order,airport,airport_code,parent,category,coalesce(bin,6) bin,count(*) records,sum(Passengers) sampled_passengers,
 sum(Passengers*MktFare) sampled_revenue,sum(Passengers*NonStopMiles) sampled_od_miles,
 100*sum(Passengers*MktFare)/sum(Passengers*NonStopMiles) yield_cents
 FROM x WHERE category IS NOT NULL GROUP BY GROUPING SETS ((panel,display_order,airport,airport_code,parent,category,bin),(panel,display_order,airport,airport_code,parent,category))''')
for table in ['pairs','selection_universe','benchmark','comparisons','origins','boardings','traffic']:
 con.execute(f"COPY {table} TO '{OUT}/{table}.csv' (HEADER,FORMAT CSV)")
audit={}
def auditq(key,sql):audit[key]=con.execute(sql).fetchdf().to_dict('records')
auditq('fare_coverage', '''SELECT count(*) records,sum(Passengers) sampled_directional_passengers,count(DISTINCT parent) parent_groups,count(DISTINCT (a,b)) airport_pairs FROM fare_sample''')
auditq('raw_fare_coverage','SELECT count(*) records,sum(Passengers) sampled_passengers FROM market')
auditq('selected_pairs','SELECT * FROM selected ORDER BY display_order')
auditq('historical_pairs','SELECT * FROM historical ORDER BY display_order')
auditq('threshold_candidates','SELECT count(*) n FROM selection_universe WHERE actual_segment_boardings>=2500000 AND origin_share>=0.5')
auditq('merger_group_traffic',f"SELECT carrier,sum(Passengers) sampled_passengers FROM clean WHERE carrier IN ('AS','HA') GROUP BY carrier")
auditq('boarding_coverage', "SELECT (SELECT sum(passengers) FROM boardings) survey_coupon_passengers,(SELECT sum(actual_segment_boardings) FROM traffic) scheduled_t100_segment_passengers")
auditq('unknown_ticket_origins',"SELECT count(*) n,coalesce(sum(Passengers),0) passengers FROM ticket_orig WHERE first_carrier IN ('','99','--')")
auditq('distance_boundaries','SELECT NonStopMiles,count(*) records FROM fare_sample WHERE NonStopMiles IN (200,500,1000,1500,2000) GROUP BY ALL ORDER BY NonStopMiles')
# Checks: share sums, bin totals, and partition at each airport.
for table,col in [('origins','origin_share'),('boardings','coupon_boarding_share')]:
 err=con.execute(f'SELECT max(abs(s-1)) FROM (SELECT airport,sum({col}) s FROM {table} GROUP BY airport)').fetchone()[0]
 assert err<1e-9; audit[table+'_max_share_sum_error']=err
 assert con.execute(f'SELECT count(*) FROM {table} WHERE {col}<0 OR {col}>1.000000001').fetchone()[0]==0
for table,keys in [('benchmark',''),('comparisons','panel,airport,parent,category,')]:
 q=f'''SELECT count(*) FROM (SELECT {keys}sum(CASE WHEN bin<6 THEN sampled_passengers ELSE -sampled_passengers END) err FROM {table} GROUP BY ALL HAVING abs(err)>1e-7)'''
 assert con.execute(q).fetchone()[0]==0
assert con.execute('SELECT count(*) FROM comparisons WHERE sampled_od_miles<=0 OR yield_cents<=0 OR NOT isfinite(yield_cents)').fetchone()[0]==0
for row in con.execute('SELECT panel,airport, sum(sampled_passengers) FROM comparisons WHERE bin=6 AND category IN (1,2) GROUP BY ALL').fetchall():
 n=con.execute('SELECT sum(Passengers) FROM fare_sample WHERE ? IN (OriginAirportID,DestAirportID)',[row[1]]).fetchone()[0];assert abs(row[2]-n)<1e-7
# Explicit declared contrasts; no hypothesis/sign assumption.
auditq('overall_contrasts','''SELECT p.panel,p.airport_code,p.parent,a.yield_cents away_yield,d.yield_cents dominant_at_yield,o.yield_cents others_at_yield,
 100*(d.yield_cents/a.yield_cents-1) at_vs_away_pct,100*(d.yield_cents/o.yield_cents-1) at_vs_others_pct
 FROM pairs p JOIN comparisons a ON p.panel=a.panel AND p.airport=a.airport AND a.category=0 AND a.bin=6
 JOIN comparisons d ON p.panel=d.panel AND p.airport=d.airport AND d.category=1 AND d.bin=6
 JOIN comparisons o ON p.panel=o.panel AND p.airport=o.airport AND o.category=2 AND o.bin=6 ORDER BY p.panel,p.display_order''')
auditq('bin_signs','''SELECT p.panel,p.airport_code,count(*) comparable_bins,count(*) FILTER(WHERE d.yield_cents>a.yield_cents) at_above_away,count(*) FILTER(WHERE d.yield_cents>o.yield_cents) at_above_others FROM pairs p
 JOIN comparisons a ON p.panel=a.panel AND p.airport=a.airport AND a.category=0 AND a.bin<6
 JOIN comparisons d ON p.panel=d.panel AND p.airport=d.airport AND d.category=1 AND d.bin=a.bin
 JOIN comparisons o ON p.panel=o.panel AND p.airport=o.airport AND o.category=2 AND o.bin=a.bin GROUP BY p.panel,p.airport_code ORDER BY p.panel,p.airport_code''')
(OUT/'validation.json').write_text(json.dumps(audit,indent=2,default=str)+'\n')
for key in ['selected_pairs','historical_pairs','fare_coverage','overall_contrasts','bin_signs']:print(key,json.dumps(audit[key],indent=2),flush=True)
