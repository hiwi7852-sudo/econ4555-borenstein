"""Passenger-weighted descriptive fare comparisons using validated coupon-path proxies."""
from pathlib import Path
import json
import duckdb
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/part3-q9';OUT.mkdir(parents=True,exist_ok=True)
c=duckdb.connect(str(ROOT/'work/q4.duckdb'),read_only=True)
c.execute("SET memory_limit='2GB'; SET threads=2")
c.execute(f"SET temp_directory='{ROOT}/work/q9-spill'")
# Check the actual coupon endpoints, ordering and intermediate airport, rather than only a count.
c.execute('''CREATE TEMP TABLE path AS SELECT Year,Quarter,ItinID,MktID,count(*) coupons,
arg_min(OriginAirportID,SeqNum) first_origin,arg_max(DestAirportID,SeqNum) last_dest,
arg_min(DestAirportID,SeqNum) first_dest,arg_max(OriginAirportID,SeqNum) last_origin,
min(SeqNum) first_seq,max(SeqNum) last_seq
FROM coupon GROUP BY ALL''')
c.execute('''CREATE TEMP TABLE q9 AS SELECT m.*,p.first_dest intermediate_airport,
CASE WHEN MktCoupons=1 THEN 'One coupon: nonstop proxy' ELSE 'Two coupons: connecting proxy' END travel_group
FROM clean m JOIN path p USING(Year,Quarter,ItinID,MktID)
WHERE p.coupons=m.MktCoupons AND p.first_origin=m.OriginAirportID AND p.last_dest=m.DestAirportID
AND (p.coupons=1 OR (p.coupons=2 AND p.last_seq=p.first_seq+1 AND p.first_dest=p.last_origin
AND p.first_dest NOT IN (m.OriginAirportID,m.DestAirportID)))''')
audit={}
def q(key,sql):
 x=c.execute(sql).fetchdf();audit[key]=x.to_dict('records');print(key,x.to_string(index=False),flush=True);return x
q('path_attrition','SELECT (SELECT count(*) FROM clean) clean_records,(SELECT count(*) FROM q9) path_valid_records,(SELECT sum(Passengers) FROM clean) clean_passengers,(SELECT sum(Passengers) FROM q9) path_valid_passengers')
raw=q('raw_comparison','''SELECT travel_group,count(*) fare_records,sum(Passengers) sampled_directional_passengers,
sum(Passengers*MktFare)/sum(Passengers) mean_fare,
sum(Passengers*NonStopMiles)/sum(Passengers) mean_nonstop_distance,
sum(Passengers*MktMilesFlown/NonStopMiles)/sum(Passengers) mean_circuity FROM q9 GROUP BY ALL ORDER BY travel_group''')
raw.to_csv(OUT/'raw_comparison.csv',index=False)
for label,keys in [('airport_pair','a,b'),('directed_airport_pair','OriginAirportID,DestAirportID'),('airport_pair_carrier','a,b,carrier')]:
 c.execute(f'''CREATE OR REPLACE TEMP TABLE cells AS SELECT {keys},MktCoupons,sum(Passengers) n,
 sum(Passengers*MktFare)/sum(Passengers) mean_fare FROM q9 GROUP BY ALL''')
 c.execute(f'''CREATE OR REPLACE TEMP TABLE matched AS SELECT {keys},max(CASE WHEN MktCoupons=1 THEN n END) n_one,
 max(CASE WHEN MktCoupons=2 THEN n END) n_two,max(CASE WHEN MktCoupons=1 THEN mean_fare END) fare_one,
 max(CASE WHEN MktCoupons=2 THEN mean_fare END) fare_two FROM cells GROUP BY ALL HAVING count(*)=2''')
 x=q(label,'''WITH weighted AS (SELECT count(*) matched_cells,sum(n_one) n_one,sum(n_two) n_two,
 sum((n_one+n_two)*fare_one)/sum(n_one+n_two) standardized_one_coupon_fare,
 sum((n_one+n_two)*fare_two)/sum(n_one+n_two) standardized_two_coupon_fare,
 sum((n_one+n_two)*CASE WHEN fare_two>fare_one THEN 1 ELSE 0 END)/sum(n_one+n_two) weight_fraction_two_more_expensive,
 count(*) FILTER(WHERE fare_two>fare_one) cells_two_more_expensive
 FROM matched) SELECT *,standardized_two_coupon_fare-standardized_one_coupon_fare dollar_difference,
 100*(standardized_two_coupon_fare/standardized_one_coupon_fare-1) percent_difference FROM weighted''')
 x.to_csv(OUT/(label+'_summary.csv'),index=False)
 c.execute(f"COPY matched TO '{OUT}/{label}_matched_cells.csv' (HEADER,FORMAT CSV)")
 # Each standardized contrast is the average within-cell difference using identical total-traffic weights.
 v=c.execute('''SELECT sum((n_one+n_two)*(fare_two-fare_one))/sum(n_one+n_two) FROM matched''').fetchone()[0]
 assert abs(v-float(x.dollar_difference.iloc[0]))<1e-8
 assert c.execute('SELECT count(*) FROM matched WHERE n_one<=0 OR n_two<=0 OR fare_one<=0 OR fare_two<=0').fetchone()[0]==0
assert raw.fare_records.sum()==audit['path_attrition'][0]['path_valid_records']
audit['methodology']={'source':'Full validated clean Market table, not one-carrier regression baseline','groups':'One or two market coupons with validated air-coupon paths; neither proves flight continuity or plane changes','fare':'Allocated directional Market fare in nominal dollars, passenger-weighted arithmetic mean','matching_weights':'For each common cell, W=n_one+n_two; use the identical W distribution for each group, then compare standardized means','baseline_restrictions':'Credible nonbulk domestic fares >=$20; no ticketing-carrier change; one/two air coupons; complete valid operations matches','causal_claim':False}
(OUT/'results.json').write_text(json.dumps(audit,indent=2,allow_nan=False)+'\n')
