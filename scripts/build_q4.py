"""Construct Q4 reduced-control pilot, including explicitly named proxy and coverage fields."""
from prepare_q4 import con,WORK,ROOT,RAW
import json
OUT=ROOT/'data/processed/2025Q2';OUT.mkdir(parents=True,exist_ok=True)
audit={}
def sql(s):con.execute(s)
def stat(name,q):
 x=con.execute(q).fetchdf();audit[name]=x.to_dict('records');print(name,x.to_string(index=False),flush=True)
# Uniqueness is a prerequisite for the many-to-one joins.
for table,keys in [('ticket','Year,Quarter,ItinID'),('market','Year,Quarter,ItinID,MktID'),('coupon','Year,Quarter,ItinID,SeqNum')]:
 assert con.execute(f'SELECT count(*) FROM (SELECT {keys},count(*) n FROM {table} GROUP BY ALL HAVING n>1)').fetchone()[0]==0
stat('raw_totals','SELECT count(*) rows,sum(Passengers) sampled_directional_passengers FROM market')
stat('ticket_join','SELECT count(*) market_rows,count(t.ItinID) ticket_matches,sum(CASE WHEN t.ItinID IS NULL THEN m.Passengers ELSE 0 END) unmatched_passengers FROM market m LEFT JOIN ticket t USING(Year,Quarter,ItinID)')
# Ticket origins counted once, marketed by first coupon, no operator-to-parent guess.
sql('''CREATE OR REPLACE TABLE ticket_orig AS SELECT t.*,c.TkCarrier first_carrier FROM ticket t JOIN coupon c USING(Year,Quarter,ItinID) WHERE c.SeqNum=1''')
stat('ticket_first_coupon','SELECT count(*) rows,count(*) FILTER (WHERE first_carrier<>RPCarrier) reporting_vs_first_marketing_differences FROM ticket_orig')
sql('''CREATE OR REPLACE TABLE airport_share AS WITH counts AS (
SELECT OriginAirportID airport,first_carrier carrier,sum(Passengers) n FROM ticket_orig
WHERE Passengers>0 AND ItinGeoType IN (1,2) AND OriginCountry='US' AND DollarCred=1 AND BulkFare=0 AND first_carrier NOT IN ('','99') GROUP BY ALL)
SELECT *,n/sum(n) OVER(PARTITION BY airport) share FROM counts''')
sql('''CREATE OR REPLACE TABLE airport_hhi AS SELECT airport,sum(share*share) hhi FROM airport_share GROUP BY airport''')
# Broad share denominator before low-fare/coupon-count/operations exclusions.
sql('''CREATE OR REPLACE TABLE broad AS SELECT m.*,least(m.OriginAirportID,m.DestAirportID) a,greatest(m.OriginAirportID,m.DestAirportID) b,
m.TkCarrier carrier,t.OriginAirportID ticket_origin,t.DollarCred,t.RoundTrip,t.ItinFare,t.Passengers ticket_pax
FROM market m JOIN ticket t USING(Year,Quarter,ItinID)
WHERE m.Passengers>0 AND m.ItinGeoType IN (1,2) AND m.MktGeoType IN (1,2) AND m.OriginCountry='US' AND m.DestCountry='US'
AND m.OriginAirportID<>m.DestAirportID AND m.TkCarrierChange=0 AND m.TkCarrier NOT IN ('','99') AND m.BulkFare=0 AND t.BulkFare=0 AND t.DollarCred=1 AND m.MktFare>0''')
stat('broad_denominator','SELECT count(*) rows,sum(Passengers) passengers,count(*) FILTER(WHERE Passengers<>ticket_pax) passenger_discrepancies FROM broad')
sql('''CREATE OR REPLACE TABLE route_share AS WITH counts AS (SELECT a,b,carrier,sum(Passengers) n FROM broad GROUP BY ALL)
SELECT *,n/sum(n) OVER(PARTITION BY a,b) RouteShare FROM counts''')
sql('''CREATE OR REPLACE TABLE route_hhi AS SELECT a,b,sum(RouteShare*RouteShare) RouteHerf FROM route_share GROUP BY ALL''')
sql('''CREATE OR REPLACE TABLE endpoint_weight AS SELECT a,b,
sum(CASE WHEN ticket_origin=a THEN Passengers ELSE 0 END)/nullif(sum(CASE WHEN ticket_origin IN (a,b) THEN Passengers ELSE 0 END),0) wa,
sum(CASE WHEN ticket_origin NOT IN (a,b) THEN Passengers ELSE 0 END)/sum(Passengers) third_origin_fraction FROM broad GROUP BY ALL''')
# Scheduled passenger operations, ratio of quarter totals, no unweighted monthly mean.
stat('t100_service_classes','SELECT Class,count(*) rows,sum(Passengers) passengers,sum(Seats) seats FROM t100 GROUP BY ALL ORDER BY Class')
sql('''CREATE OR REPLACE TABLE ops AS SELECT Year,Quarter,Unique_Carrier operator,Origin_Airport_ID origin_id,Dest_Airport_ID dest_id,
sum(Passengers) pax,sum(Seats) seats,sum(Departures_Performed) departures,sum(Passengers)/sum(Seats) lf
FROM t100 WHERE Class IN ('A','C','E','F') AND Seats>0 AND Departures_Performed>0 AND Passengers>=0
GROUP BY ALL''')
stat('t100_raw_duplicate_rows', 'SELECT sum(n-1) duplicates FROM (SELECT *,count(*) n FROM t100 GROUP BY ALL HAVING n>1)')
stat('positive_scheduled_duplicate_rows', "SELECT coalesce(sum(n-1),0) duplicates FROM (SELECT *,count(*) n FROM t100 WHERE Class IN ('A','C','E','F') AND Seats>0 AND Departures_Performed>0 GROUP BY ALL HAVING n>1)")
stat('ops_quality','SELECT count(*) keys,count(*) FILTER(WHERE lf>1) load_factors_above_one,min(lf) min_lf,max(lf) max_lf FROM ops')
# Match Coupon to segment operations using its actual operating carrier and airport IDs.
sql('''CREATE OR REPLACE TABLE coupon_service AS SELECT c.Year,c.Quarter,c.ItinID,c.MktID,count(*) ncoupons,
count(*) FILTER(WHERE o.operator IS NOT NULL AND o.lf>0 AND o.lf<=1) matched_coupons,
sum(CASE WHEN o.lf>0 AND o.lf<=1 THEN c.Distance*o.lf ELSE 0 END)/nullif(sum(c.Distance),0) partial_lf,
bool_and(c.CouponType='A' AND c.Distance>0 AND c.OriginCountry='US' AND c.DestCountry='US') all_air,
sum(c.Distance) coupon_distance,min(c.SeqNum) first_seq,max(c.SeqNum) last_seq
FROM coupon c LEFT JOIN ops o ON c.Year=o.Year AND c.Quarter=o.Quarter AND c.OpCarrier=o.operator AND c.OriginAirportID=o.origin_id AND c.DestAirportID=o.dest_id GROUP BY c.Year,c.Quarter,c.ItinID,c.MktID''')
stat('coupon_ops_match','SELECT sum(ncoupons) coupons,sum(matched_coupons) matched_coupons,count(*) markets,count(*) FILTER(WHERE ncoupons=matched_coupons) fully_matched_markets FROM coupon_service')
sql('''CREATE OR REPLACE TABLE candidates AS SELECT b.*,s.ncoupons,s.matched_coupons,s.all_air,s.coupon_distance,
CASE WHEN s.ncoupons=s.matched_coupons THEN s.partial_lf END LoadFactor,
b.MktMilesFlown/b.NonStopMiles Circuity,b.MktCoupons-1 Stops_coupon_proxy
FROM broad b LEFT JOIN coupon_service s USING(Year,Quarter,ItinID,MktID)''')
criteria=[('broad','true'),('positive_distance','NonStopMiles>0 AND MktMilesFlown>0'),('fare_at_least_20','MktFare>=20'),('one_or_two_air_coupons','MktCoupons BETWEEN 1 AND 2 AND ncoupons=MktCoupons AND all_air'),('complete_operations','LoadFactor>0 AND LoadFactor<=1')]
where=[]
for name,expr in criteria:
 where.append('('+expr+')');stat('attrition_'+name,'SELECT count(*) rows,sum(Passengers) passengers FROM candidates WHERE '+' AND '.join(where))
sql('CREATE OR REPLACE TABLE clean AS SELECT * FROM candidates WHERE '+' AND '.join(where))
stat('distance_checks','SELECT count(*) FILTER(WHERE Circuity<1) circuity_below_one,min(Circuity) min_circuity,max(Circuity) max_circuity,max(abs(MktMilesFlown-coupon_distance)) max_market_coupon_distance_difference FROM clean')
# Weighted inverse empirical CDF: smallest fare with cumulative passengers >= p*N.
sql('''CREATE OR REPLACE TABLE fare_cdf AS WITH f AS (SELECT a,b,carrier,MktFare,sum(Passengers) n FROM clean GROUP BY ALL)
SELECT *,sum(n) OVER(PARTITION BY a,b,carrier ORDER BY MktFare ROWS UNBOUNDED PRECEDING) cum_n,sum(n) OVER(PARTITION BY a,b,carrier) total_n FROM f''')
sql('''CREATE OR REPLACE TABLE fares AS SELECT a,b,carrier,min(MktFare) FILTER(WHERE cum_n>=0.2*total_n) P20,
min(MktFare) FILTER(WHERE cum_n>=0.5*total_n) P50,min(MktFare) FILTER(WHERE cum_n>=0.8*total_n) P80 FROM fare_cdf GROUP BY ALL''')
sql('''CREATE OR REPLACE TABLE services AS SELECT a,b,carrier,sum(Passengers) sampled_passengers,count(*) fare_records,
sum(Passengers*NonStopMiles)/sum(Passengers) Distance,sum(Passengers*LoadFactor)/sum(Passengers) LoadFactor,
sum(Passengers*Circuity)/sum(Passengers) Circuity,sum(Passengers*Stops_coupon_proxy)/sum(Passengers) Stops_coupon_proxy FROM clean GROUP BY ALL''')
sql('''CREATE OR REPLACE TABLE q4 AS SELECT 2025 AS "Year",2 AS "Quarter",s.*,f.P20,f.P50,f.P80,ln(f.P20) ln_P20,ln(f.P50) ln_P50,ln(f.P80) ln_P80,
ln(s.Distance) ln_Distance,ln(s.LoadFactor) ln_LoadFactor,ln(s.Circuity) ln_Circuity,
r.RouteShare,h.RouteHerf,w.wa endpoint_a_weight,w.third_origin_fraction,
CASE WHEN ha.airport IS NOT NULL AND hb.airport IS NOT NULL THEN w.wa*coalesce(sa.share,0)+(1-w.wa)*coalesce(sb.share,0) END OrgShare,
w.wa*ha.hhi+(1-w.wa)*hb.hhi OrgHerf,
10*r.n/91 estimated_daily_passengers, (10*r.n/91>=10 AND r.RouteShare>=0.1) eligible,
s.carrier carrier_fe,s.a endpoint_a_fe,s.b endpoint_b_fe,
CAST(NULL AS DOUBLE) Stops_on_plane
FROM services s JOIN fares f USING(a,b,carrier) JOIN route_share r USING(a,b,carrier) JOIN route_hhi h USING(a,b) JOIN endpoint_weight w USING(a,b)
LEFT JOIN airport_share sa ON s.a=sa.airport AND s.carrier=sa.carrier LEFT JOIN airport_share sb ON s.b=sb.airport AND s.carrier=sb.carrier
LEFT JOIN airport_hhi ha ON s.a=ha.airport LEFT JOIN airport_hhi hb ON s.b=hb.airport''')
sql('''CREATE OR REPLACE TABLE baseline AS SELECT * EXCLUDE(rn) FROM (
SELECT *,row_number() OVER(PARTITION BY a,b ORDER BY md5('42:'||a::VARCHAR||':'||b::VARCHAR||':'||carrier)) rn FROM q4 WHERE eligible AND OrgShare IS NOT NULL AND OrgHerf IS NOT NULL) WHERE rn=1''')
for table,name in [('q4','q4_all_carriers'),('baseline','q4_baseline_one_carrier_per_route'),('airport_share','airport_origination_shares'),('route_share','route_shares'),('ops','t100_quarter_segment_operations')]:
 con.execute(f"COPY {table} TO '{OUT}/{name}.csv' (HEADER,FORMAT CSV)")
stat('output_counts','SELECT count(*) carrier_routes,count(*) FILTER(WHERE eligible) eligible_carrier_routes,count(*) FILTER(WHERE OrgShare IS NULL OR OrgHerf IS NULL) missing_origin_variables,sum(sampled_passengers) sampled_passengers FROM q4')
stat('baseline_count','SELECT count(*) routes FROM baseline')
stat('shares_validation','SELECT min(RouteShare) min_route_share,max(RouteShare) max_route_share,min(RouteHerf) min_route_hhi,max(RouteHerf) max_route_hhi,min(OrgShare) min_org_share,max(OrgShare) max_org_share,min(OrgHerf) min_org_hhi,max(OrgHerf) max_org_hhi FROM q4')
for table,group,col in [('route_share','a,b','RouteShare'),('airport_share','airport','share')]:
 err=con.execute(f'SELECT max(abs(n-1)) FROM (SELECT {group},sum({col}) n FROM {table} GROUP BY ALL)').fetchone()[0];assert err<1e-9
for col in ['RouteShare','RouteHerf','OrgShare','OrgHerf']:
 assert con.execute(f'SELECT count(*) FROM q4 WHERE {col}<0 OR {col}>1.000000001').fetchone()[0]==0
assert con.execute('SELECT count(*) FROM baseline WHERE NOT(P20<=P50 AND P50<=P80) OR ln_P20 IS NULL OR ln_LoadFactor IS NULL').fetchone()[0]==0
stat('summary','SELECT min(Distance) min_distance,max(Distance) max_distance,min(LoadFactor) min_lf,max(LoadFactor) max_lf,min(Stops_coupon_proxy) min_stops_proxy,max(Stops_coupon_proxy) max_stops_proxy FROM baseline')
stat('coupon_marketing_consistency', 'SELECT count(*) coupon_rows,count(*) FILTER(WHERE c.TkCarrier<>m.carrier) carrier_differences FROM clean m JOIN coupon c USING(Year,Quarter,ItinID,MktID)')
stat('origin_missing_reasons', 'SELECT count(*) FILTER(WHERE wa IS NULL) routes_without_endpoint_origins,count(*) FILTER(WHERE third_origin_fraction>0) routes_with_third_origins,max(third_origin_fraction) max_third_origin_fraction FROM endpoint_weight')
stat('baseline_missing', 'SELECT count(*) rows,count(*) FILTER(WHERE Stops_on_plane IS NULL) missing_on_plane_stops,count(*) FILTER(WHERE ln_P20 IS NULL OR ln_P50 IS NULL OR ln_P80 IS NULL OR ln_Distance IS NULL OR ln_LoadFactor IS NULL OR ln_Circuity IS NULL OR RouteShare IS NULL OR RouteHerf IS NULL OR OrgShare IS NULL OR OrgHerf IS NULL OR Stops_coupon_proxy IS NULL) incomplete_proxy_spec_rows FROM baseline')
stat('ops_above_one', 'SELECT * FROM ops WHERE lf>1')
stat('raw_t100_duplicate_detail', 'SELECT *,count(*) n FROM t100 GROUP BY ALL HAVING n>1')
assert audit['baseline_missing'][0]['incomplete_proxy_spec_rows']==0
assert audit['coupon_marketing_consistency'][0]['carrier_differences']==0
(OUT/'validation-q4.json').write_text(json.dumps(audit,indent=2,default=str))
print('Wrote',OUT,flush=True)
