"""Render validated modern Table 1 results to a standalone LaTeX document."""
from pathlib import Path
import json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/part3-q5'
pairs=pd.read_csv(OUT/'pairs.csv');comp=pd.read_csv(OUT/'comparisons.csv');bench=pd.read_csv(OUT/'benchmark.csv');audit=json.loads((OUT/'validation.json').read_text())
names={'AA':'American','UA':'United','DL':'Delta','WN':'Southwest','AS_HA':'Alaska--Hawaiian'}
airports={'DFW':'Dallas/Fort Worth','CLT':'Charlotte','EWR':'Newark','IAH':'Houston Intercontinental','BWI':'Baltimore/Washington','DTW':'Detroit','STL':'St. Louis','MSP':'Minneapolis/St. Paul','PIT':'Pittsburgh','ORD':"Chicago O'Hare",'ATL':'Atlanta'}
def val(rows,i):
 r=rows[rows.bin==i]
 if r.empty:return r'\textemdash'
 assert len(r)==1
 x=r.iloc[0];s=f'{x.yield_cents:.2f}'
 return s+(r'$^{\dagger}$' if x.sampled_passengers<30 else '')
def table(panel,title,subtitle):
 s=r'''\begin{center}
{\Large\bfseries '''+title+r'''}\\[4pt]
{\large 2025 Q2: April--June}\\[3pt]
\textit{Fares in nominal cents per nonstop O\&D passenger-mile}
\end{center}
\noindent '''+subtitle+r'''
\begin{center}
\small
\setlength{\tabcolsep}{3.5pt}
\renewcommand{\arraystretch}{1.08}
\begin{tabular}{@{}lrrrrrrr@{}}
\toprule
 & \multicolumn{7}{c}{Nonstop origin--destination distance (miles)}\\
\cmidrule(l){2-8}
Fare comparison & $<200$ & $200$--$<500$ & $500$--$<1000$ & $1000$--$<1500$ & $1500$--$<2000$ & $\geq2000$ & All\\
\midrule
Eligible domestic O\&D & '''+' & '.join(val(bench,i) for i in range(7))+r' \\'+'\n'
 for p in pairs[pairs.panel==panel].sort_values('display_order').itertuples():
  carrier=names.get(p.parent,p.parent);a=p.airport_code
  s+=r'\addlinespace[5pt]'+'\n'+r'\multicolumn{8}{@{}l}{\textbf{'+carrier+' --- '+airports[a]+' ('+a+r')}}\\'+'\n'
  s+=r'\multicolumn{8}{@{}l}{\footnotesize '+f'Origination share: {100*p.origin_share:.1f}'+r'\%; coupon-boarding share (proxy): '+f'{100*p.coupon_boarding_share:.1f}'+r'\%; T-100 boardings: '+f'{p.actual_segment_boardings/1e6:.2f}'+r' million}\\'+'\n'
  for cat,label in [(0,f'{p.parent} away from {a}'),(1,f'{p.parent} to/from {a}'),(2,f'Others to/from {a}')]:
   rows=comp[(comp.panel==panel)&(comp.airport==p.airport)&(comp.category==cat)]
   s+=label+' & '+' & '.join(val(rows,i) for i in range(7))+r' \\'+'\n'
 s+=r'''\bottomrule
\end{tabular}
\end{center}
\vspace{-0.4em}
{\footnotesize\noindent\textbf{Reading the table.} Each block compares the same carrier away from the airport, that carrier on O\&D markets touching the airport, and every other eligible carrier on those markets. Yield = 100 $\times$ weighted fare revenue / weighted nonstop O\&D miles. The ``All'' column is recalculated from totals, not averaged across bins. A dash means no eligible fare records; $\dagger$ indicates fewer than 30 sampled directional passengers. Shares are percentages. Coupon-boarding shares are survey proxies, not observed T-100 marketing-carrier shares. T-100 boardings are scheduled domestic airport-wide segment passengers. Full methods and limitations follow.\par}
'''
 return s
tex=r'''\documentclass[10pt]{article}
\usepackage[letterpaper,margin=0.6in]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern,booktabs,microtype,amsmath}
\usepackage{enumitem}
\setlist{nosep,leftmargin=*}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\begin{document}
'''
tex+=table('A','ECON 4555 --- Part III, Question 5',r'\textbf{Table 1. Modern dominated-airport comparisons.} Airports have at least 2.5 million scheduled domestic boardings in the quarter and a carrier with at least 50\% of observed ticket originations. The six highest origination shares are shown; selection does not use fares.')
tex+=r'''\medskip
\textbf{Main findings.} The selected carrier's overall yield exceeds rivals' at all six airports (by 32.3--76.8\%). Its yield also exceeds its own away-airport yield at five airports, but is 8.4\% lower at EWR. Distance-specific comparisons contain further reversals. These are descriptive differences across travel mixes, not estimates of market-power effects.
\newpage
'''
tex+=table('B','Historical-airport follow-up',r'\textbf{Supplement to Table 1.} The six airports in Borenstein\textquotesingle s original Table 1, in their original order, paired with the largest observed ticket-origination group in 2025 Q2. This contextual panel does not impose the main panel\textquotesingle s traffic or 50\% dominance thresholds; PIT and ORD have leading shares below 50\%.')
tex+=r'''\medskip
\textbf{Historical continuity is not assumed.} TWA and USAir are absorbed into today's American group, and Northwest into Delta; their former airport positions do not automatically transfer to those successors. The data identify Southwest as the current leader at STL and PIT. At STL and PIT, Southwest's overall yield is respectively 1.6\% and 9.1\% below other eligible carriers at the same airport.
\newpage
\begin{center}{\Large\bfseries Methodology and comparability}\end{center}
\textbf{Original reference.} Borenstein (1989), \emph{RAND Journal of Economics}, 20(3), Table 1, printed p.~356 (PDF p.~14). The original compares six dominant carrier--airport pairs, each against the carrier elsewhere and other airlines at that airport, by nonstop-distance band. Its fares are from domestic DB1A tickets in 1987 Q3. The present table preserves that comparison using DB1B in 2025 Q2.

\textbf{Fare sample and benchmark.} Use all 7,675,361 validated, eligible directional Market records (14,215,332 sampled passenger weights; 28,910 unordered airport pairs and 18 parent groups), not the 7,499-row one-carrier regression baseline. The latter would exclude competing fare observations. Retain domestic, credible nonbulk fares, no ticketing-carrier change, fares at least \$20 per directional market, one/two validated air coupons, positive distances and complete valid operating-segment matches. These inherited filters retain about 88.1\% of raw DB1B directional passenger weights; the benchmark is all \emph{eligible survey O\&D traffic}, not a census of every domestic passenger. All eligible competitors enter ``Others.''

\textbf{Yield definition.} For each row and distance band, with survey passenger weight $p_i$, allocated directional fare $F_i$, and nonstop O\&D miles $d_i$,
\[
Y=100\frac{\sum_i p_iF_i}{\sum_i p_id_i}\quad\text{cents per nonstop O\&D passenger-mile}.
\]
This is a passenger-mile-weighted mean of individual fare-per-mile ratios, not an unweighted mean of route fare percentiles. DB1B Market fares already allocate ticket revenue by flown distance; they are not halved again for round trips. Both directional markets of a round trip contribute intentionally. The common 10\% survey expansion factor cancels. ``To/from'' refers to O\&D endpoints; connecting through an airport alone does not put the fare in its to/from row. Bins are $[0,200)$, $[200,500)$, $[500,1000)$, $[1000,1500)$, $[1500,2000)$, and $[2000,\infty)$; boundaries are explicitly nonoverlapping. The original table note specifies nonstop miles but does not fully detail its averaging weights; the weighting here is explicit.

\textbf{Airport shares and selection.} Count each credible nonbulk domestic Ticket once at its true ticket origin, weighted by passengers and assigned to its first coupon's ticketing carrier. Aggregate to parent groups before forming shares. Denominators include all valid groups and precede fare/service restrictions. The boarding proxy similarly uses passenger-weighted domestic air Coupons, grouped by coupon origin and ticketing parent, including transfers. It can miss within-coupon on-plane stops and is affected by survey coverage. It is \emph{not} a T-100 marketing-network enplanement measure. T-100 supplies the 2.5-million boarding selection threshold: sum April--June scheduled passenger segment counts across operators, aircraft and configurations, with positive seats/departures. Shared regional operators are not assigned wholesale to a major airline. All 13 eligible carrier--airport candidates are ranked by origination share, then airport traffic and codes; the top six are displayed. No fare values enter selection.

\textbf{Mergers and corporate groups as of 2025 Q2.}
\begin{center}\small
\begin{tabular}{@{}ll@{}}
\toprule
Modern group & Treatment of historical consolidation\\
\midrule
American (AA) & Includes integrated TWA and US Airways/Piedmont lineages.\\
Delta (DL) & Includes integrated Northwest lineage.\\
United (UA) & Includes integrated Continental lineage.\\
Southwest (WN) & Includes integrated AirTran lineage.\\
Alaska--Hawaiian (AS+HA) & Alaska (including Virgin America) plus Hawaiian under one parent.\\
Other groups & Keep other ticketing codes separate, including B6, NK and F9.\\
\bottomrule
\end{tabular}
\end{center}
Historical TW, NW, US, CO and FL codes are not present in the current eligible fare records, so no fictitious predecessor observations are added. AS and HA remain separate operating brands in the source quarter but are combined for this parent-level descriptive table; the previous Q4 baseline is unchanged. Regional flights marketed by a major group follow their observed ticketing code. Shared operators such as SkyWest are not treated as a single major's subsidiary; alliances and codeshares alone do not establish common ownership.

\textbf{Limits.} Nominal 2025 and 1987 cents-per-mile values are not inflation-adjusted comparisons. The paper's preprocessed DB1A one-way/round-trip fares differ from DB1B mileage-prorated market fares; we do not reproduce its half-round-trip allocation or its exclusion of open-jaw/circle tickets. BTS fare-class codes are not comparable across carriers, so first class cannot be reliably excluded. One/two coupons do not prove at most one plane change. Ancillary fees are not measured. Different destinations, distance mixes, trip structures and service quality can drive differences even within a distance band. No route-matched premium, regression, causal effect, markup or welfare calculation is claimed.

{\footnotesize\textit{Reproduction and audit:} \texttt{scripts/table1\_part3\_q5.py} and \texttt{scripts/render\_table1\_part3\_q5.py}; output CSVs include each cell's fare records, sampled passenger weights, revenue and O\&D miles. Share sums, distance-bin totals and carrier/competitor partitions are checked. Sources: the repository's Borenstein PDF and validated official BTS DB1B/T-100 archives, with acquisition hashes recorded in project documentation.}
\end{document}
'''
(OUT/'modern_table1.tex').write_text(tex)
# Record input identity without rereading the multi-gigabyte processing database.
manifest=ROOT/'docs/acquisition-validated-2025Q2.json'
(OUT/'provenance.json').write_text(json.dumps(dict(source_database='work/q4.duckdb',fare_table='clean',original_reference='Borenstein (1989), Table 1, printed p.356 / PDF p.14',source_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),selection={'minimum_quarter_boardings':2500000,'minimum_ticket_origin_share':0.5,'main_pairs':6,'ranking':'origin share descending, boardings descending, airport code, parent code'},grouping={'AS':'AS_HA','HA':'AS_HA','other_codes':'unchanged'},yield_formula='100*sum(Passengers*MktFare)/sum(Passengers*NonStopMiles)',regressions_run=False),indent=2)+'\n')
print('Wrote',OUT/'modern_table1.tex')
