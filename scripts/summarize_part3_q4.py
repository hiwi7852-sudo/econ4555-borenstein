"""Reproduce level summary statistics and LaTeX for the fixed Part II baseline; no regressions."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'data/processed/2025Q2/q4_baseline_one_carrier_per_route.csv'
out=ROOT/'reports/part3-q4';out.mkdir(parents=True,exist_ok=True)
d=pd.read_csv(source)
variables=[('P20','20th-percentile fare','Dollars',2),('P50','50th-percentile fare','Dollars',2),('P80','80th-percentile fare','Dollars',2),('Distance','Nonstop O\\&D distance','Miles',2),('LoadFactor','Load factor','Ratio (0--1)',4),('Circuity','Circuity','Ratio',4),('Stops_coupon_proxy','Coupon-stop proxy','Coupon points',4),('RouteHerf','Route HHI','Index (0--1)',4),('RouteShare','Route share','Share (0--1)',4),('OrgHerf','Airport-origin HHI','Index (0--1)',4),('OrgShare','Airport-origin share','Share (0--1)',4)]
cols=[x[0] for x in variables]
assert len(d)==7499 and not d.duplicated(['a','b']).any()
assert d.eligible.all() and (d.Year==2025).all() and (d.Quarter==2).all()
assert np.isfinite(d[cols].dropna().to_numpy()).all()
# Preserve the baseline; omit missing values separately for each summary column.
stats=d[cols].agg(['count','mean','std','min','max']).T
assert stats['count'].eq(7499).all()
assert d['Stops_on_plane'].isna().all()
assert (d.P20<=d.P50).all() and (d.P50<=d.P80).all()
for c in ['LoadFactor','RouteHerf','RouteShare','OrgHerf','OrgShare']:assert d[c].between(0,1).all()
stats.index.name='variable';stats.to_csv(out/'summary_statistics.csv',float_format='%.12g')
rows=[]
for c,label,unit,places in variables:
 r=stats.loc[c];values=[f'{r[k]:,.{places}f}' for k in ['mean','std','min','max']]
 rows.append(' & '.join([label,unit,f'{int(r["count"]):,}',*values])+r' \\')
tex=r'''\documentclass[11pt]{article}
\usepackage[letterpaper,margin=0.75in]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{booktabs}
\usepackage{microtype}
\usepackage{array}
\pagestyle{empty}
\begin{document}
\begin{center}
{\Large\bfseries ECON 4555: Part III, Question 4}\\[5pt]
{\large Summary Statistics in Levels}\\[3pt]
{2025 Q2: April--June}
\end{center}
\vspace{0.5em}
\noindent The sample is the validated Part II baseline: one eligible ticketing carrier per unordered airport pair, for a total of 7,499 observations. All continuous regression variables below are reported in levels.

\begin{table}[htbp]
\centering
\caption{Dependent and independent variables in the planned fare regression}
\label{tab:summary}
\small
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.16}
\begin{tabular}{@{}llrrrrr@{}}
\toprule
Variable & Units & $N$ & Mean & Std. dev. & Minimum & Maximum \\
\midrule
'''+ '\n'.join(rows)+r'''
\bottomrule
\end{tabular}
\end{table}

\noindent\textbf{Notes.} Statistics are unweighted across the 7,499 baseline carrier--route observations; the standard deviation uses the sample denominator $N-1$. Missing values are omitted separately for each variable. All 11 reported variables are complete, so no observations are removed from the baseline for this table. Categorical fixed-effect identifiers are not summarized as continuous variables. No regressions have been estimated.

\medskip
\noindent Fares are passenger-weighted within-carrier/route percentiles of allocated directional DB1B Market fares, in nominal dollars. The table summarizes those percentile fares across observations; it does not recalculate pooled passenger fare percentiles. Distance is nonstop origin--destination mileage. Load factor is a passenger-weighted measure of quarterly operating-segment passenger/seat ratios, with coupon-distance weights within journeys. Circuity is flown mileage divided by nonstop mileage. Slight values below one in the source distance measures are retained.

\medskip
\noindent\textbf{Stops limitation.} The coupon-stop proxy is the passenger-weighted mean of market coupons minus one. It counts intermediate coupon points, cannot distinguish on-plane stops from plane changes, and can miss stops within a coupon. True on-plane stops are unavailable in all 7,499 observations and are not treated as zero or used to delete the entire sample.

\medskip
\noindent Route and airport-origin shares and HHIs are measured on a \textbf{0--1 scale}, not as percentages or on the 0--10,000 HHI scale. Airport-origin variables combine endpoint ticket-origination measures using weights based on true ticket origins. Route and airport share denominators were constructed using the broader quarter before regression-sample restrictions.

\medskip
\noindent\textbf{Main patterns.} Mean 20th-, 50th-, and 80th-percentile fares are \$174.97, \$243.73, and \$348.04. Mean distance is 1,233 miles and mean load factor is 0.8152 (81.52\%). Mean circuity of 1.0960 implies about 9.6\% more flown mileage than nonstop mileage on average. Mean route HHI (0.5727) exceeds mean airport-origin HHI (0.3491); the selected carrier's mean route share is 0.5961. These patterns describe the selected baseline and do not establish causal effects.

\medskip
\noindent\textit{Source:} Validated BTS DB1B Market, Ticket and Coupon, and T-100 Domestic Segment data for 2025 Q2; Part II baseline file \texttt{q4\_baseline\_one\_carrier\_per\_route.csv}.
\end{document}
'''
(out/'summary_statistics.tex').write_text(tex)
(out/'summary_provenance.json').write_text(json.dumps(dict(source=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),baseline_rows=len(d),weighting='Unweighted across baseline observations',standard_deviation_ddof=1,missing_rule='Variable-wise omission; no missing values among 11 table variables',true_on_plane_stops_valid=int(d.Stops_on_plane.count()),regressions_run=False),indent=2)+'\n')
print(stats.to_string())
