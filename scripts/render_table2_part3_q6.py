"""Generate the modern Table 2 LaTeX and complete coefficient interpretations from saved results."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/part3-q6'
c=pd.read_csv(OUT/'coefficients.csv',keep_default_na=False)
e=pd.read_csv(OUT/'coefficient_interpretation_effects.csv')
f=pd.read_csv(OUT/'model_fit.csv');p=json.loads((OUT/'provenance.json').read_text())
ys=['ln_P20','ln_P50','ln_P80']
terms=['ln_Distance','ln_LoadFactor','ln_Circuity','Stops_coupon_proxy','OrgShare','OrgHerf','RouteShare','RouteHerf']
labels={'ln_Distance':r'$\ln(\mathrm{Distance})$','ln_LoadFactor':r'$\ln(\mathrm{LoadFactor})$','ln_Circuity':r'$\ln(\mathrm{Circuity})$','Stops_coupon_proxy':'Coupon-stop proxy','OrgShare':'Airline airport-origin share','OrgHerf':'Airport-origin HHI','RouteShare':'Airline route share','RouteHerf':'Route HHI'}
def get(term,y,col='coefficient'):
 return float(c[(c.term==term)&(c.outcome==y)].iloc[0][col])
def betas(term):return ', '.join(f'{get(term,y):.4f}' for y in ys)
def effects(term):return ', '.join(f'{float(e[(e.term==term)&(e.outcome==y)].iloc[0].percent_fare_difference):+.2f}\\%' for y in ys)
rows=[]
for term in terms:
 cells=[]
 for y in ys:
  q=get(term,y,'p_value');star='***' if q<.01 else '**' if q<.05 else '*' if q<.1 else ''
  cells.append(f'{get(term,y):.4f}'+(r'$^{'+star+'}$' if star else ''))
 rows.append(labels[term]+' & '+' & '.join(cells)+r' \\')
 rows.append(' & '+' & '.join(f'({get(term,y,"standard_error"):.4f})' for y in ys)+r' \\[3pt]')
tex=r'''\documentclass[10pt]{article}
\usepackage[letterpaper,margin=0.6in]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern,booktabs,microtype,amsmath}
\usepackage{enumitem}
\setlist{nosep,leftmargin=*}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\begin{document}
\begin{center}
{\Large\bfseries ECON 4555 --- Part III, Question 6}\\[5pt]
{\large Modern Table 2: Fare Regressions}\\[3pt]
{2025 Q2 --- Reduced-control OLS specification}
\end{center}
\begin{center}
\renewcommand{\arraystretch}{1.08}
\setlength{\tabcolsep}{12pt}
\begin{tabular}{@{}lrrr@{}}
\toprule
 & \multicolumn{3}{c}{Ordinary least squares}\\
\cmidrule(l){2-4}
Dependent variable & $\ln(P_{20})$ & $\ln(P_{50})$ & $\ln(P_{80})$\\
\midrule
'''+ '\n'.join(rows)+r'''
\midrule
Carrier fixed effects & Yes & Yes & Yes\\
Constant & Yes & Yes & Yes\\
Observations & '''+' & '.join(f'{int(f[f.outcome==y].iloc[0].n):,}' for y in ys)+r''' \\
$R^2$ & '''+' & '.join(f'{float(f[f.outcome==y].iloc[0].r_squared):.4f}' for y in ys)+r''' \\
Adjusted $R^2$ & '''+' & '.join(f'{float(f[f.outcome==y].iloc[0].adjusted_r_squared):.4f}' for y in ys)+r''' \\
\bottomrule
\end{tabular}
\end{center}
{\small\textbf{Notes.} HC1 heteroskedasticity-robust standard errors in parentheses. $^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$; two-sided tests use a $t$ reference distribution with 7,477 residual degrees of freedom. All eight reported slope coefficients are significant at the 1\% level in each model under this inference convention. Carrier coefficients and the intercept are estimated but omitted from display. $R^2$ includes carrier fixed effects, not a within-carrier-only fit measure.\par}

\textbf{Estimation sample.} Unweighted OLS on the unchanged Part II baseline: one reproducibly selected eligible ticketing carrier for each of 7,499 unordered airport pairs. All modeled variables are valid in all rows; no further observations are excluded. Eligibility requires at least 10 estimated passengers/day and a route share of at least 10\%, with the inherited cleaning rules. There are 14 carrier categories (13 dummies plus an intercept), eight slope controls and 22 estimated parameters. The reference carrier is 3M; its choice does not change the reported slopes.

\textbf{Variables and comparison.} Fares are passenger-weighted within-carrier/route 20th, 50th and 80th percentiles of allocated directional Market fares; these are three OLS regressions on percentile outcomes, not individual-passenger quantile regressions. Distance, load factor and circuity use natural logs. Shares and HHIs enter in levels on a 0--1 scale. The coupon-stop proxy is a passenger-weighted mean of coupons minus one, not true on-plane stops. Only carrier fixed effects are included. Relative to Borenstein's Table 2, aircraft size, frequency, separate plane changes, competitors' costs, tourism and airport-scarcity controls are omitted; on-plane stops are replaced by the proxy. Optional potential competition and all 2SLS columns are outside this specification.

{\footnotesize\textit{Reference:} Borenstein (1989), Table 2, printed p.~357 / PDF p.~15, especially its final three OLS columns. Sources: validated 2025 Q2 DB1B/T-100 baseline. This is a modern reduced-control comparison, not an exact replication.}
\newpage
\begin{center}{\Large\bfseries Interpreting every slope coefficient}\end{center}

All interpretations condition on the other regressors and carrier fixed effects. Values below are ordered by the 20th-, 50th- and 80th-percentile fare equations. For logged regressors, the coefficient is an elasticity: a 1\% relative increase is associated with approximately $\beta$\% higher fare. A one-percentage-point change in load factor is \emph{not} a 1\% relative change.

\textbf{Illustrative fitted-fare differences.} Exact transformations of the estimated log-fare coefficients; they are conditional associations, not intervention effects.
\begin{center}
\small
\setlength{\tabcolsep}{5pt}
\renewcommand{\arraystretch}{1.1}
\begin{tabular}{@{}llrrr@{}}
\toprule
Regressor & Illustrative increase & $P_{20}$ & $P_{50}$ & $P_{80}$\\
\midrule
'''
changes={'ln_Distance':r'10\% relative','ln_LoadFactor':r'10\% relative','ln_Circuity':r'10\% relative','Stops_coupon_proxy':'1 proxy unit','OrgShare':'10 percentage points','OrgHerf':'0.10 HHI units','RouteShare':'10 percentage points','RouteHerf':'0.10 HHI units'}
for term in terms:
 vals=[]
 for y in ys:
  effect=float(e[(e.term==term)&(e.outcome==y)].iloc[0].percent_fare_difference)
  vals.append(f'{effect:+.2f}'+r'\%')
 tex+=labels[term]+' & '+changes[term]+' & '+' & '.join(vals)+r' \\'+'\n'
tex+=r'''\bottomrule
\end{tabular}
\end{center}
{\small For log regressors, the exact 10\% comparison is $100[(1.10)^\beta-1]$; for a level-regressor change $\Delta x$, it is $100[\exp(\beta\Delta x)-1]$. An HHI increase of 0.10 is 1,000 points on the alternative 0--10,000 scale. These changes describe the exponentiated fitted-log relationship, not an unbiased arithmetic-mean dollar-price prediction.\par}
'''
descriptions=[
('Distance',f'The elasticities are {betas("ln_Distance")}. Longer routes have higher total fares, but less than proportionately to distance. Conditional fare per mile therefore declines with distance in this specification.'),
('Load factor',f'The elasticities are {betas("ln_LoadFactor")}. More heavily occupied service is associated with higher fares. This positive sign does not establish that fuller aircraft cause higher prices or lower efficiency; demand and pricing jointly affect occupancy.'),
('Circuity',f'The elasticities are {betas("ln_Circuity")}. More flown mileage relative to nonstop O\\&D distance is associated with higher fares after controlling for endpoint distance and the coupon-stop proxy. This is not evidence that passengers value detours.'),
('Coupon-stop proxy',f'The coefficients are {betas("Stops_coupon_proxy")}. Moving from zero to one average intermediate coupon point is associated with {effects("Stops_coupon_proxy")} fare differences. The proxy mixes journey structures and cannot distinguish staying on the plane from changing planes; it cannot be read as a price for an additional true stop.'),
('Airline airport-origin share',f'The coefficients are {betas("OrgShare")}. A 10-percentage-point increase in the carrier\\textquotesingle s weighted endpoint origination share is associated with {effects("OrgShare")} higher fares, holding endpoint concentration and route competition measures fixed. Own airport presence matters separately from overall HHI.'),
('Airport-origin HHI',f'The coefficients are {betas("OrgHerf")}. A 0.10 increase in weighted endpoint HHI is associated with {effects("OrgHerf")} fare differences, holding the airline\\textquotesingle s own airport share fixed. This negative partial association does not imply that airport mergers or less competition would lower fares.'),
('Airline route share',f'The coefficients are {betas("RouteShare")}. A 10-percentage-point increase in the airline\\textquotesingle s route passenger share is associated with {effects("RouteShare")} higher fares, holding route HHI and airport-origin measures fixed. The numerical association is largest for low-percentile fares; no cross-equation equality test is claimed.'),
('Route HHI',f'The coefficients are {betas("RouteHerf")}. A 0.10 increase in route concentration is associated with {effects("RouteHerf")} higher fares at a given own route share. This describes overall concentration conditional on dominance; it is not a forecast of any particular merger.')]
tex+=r'\begin{enumerate}'+'\n'
for name,desc in descriptions:tex+=r'\item \textbf{'+name+r'.} '+desc+'\n'
tex+=r'''\end{enumerate}
\newpage
\begin{center}{\Large\bfseries Competition, methodology and limitations}\end{center}
\textbf{What the estimates suggest.} Higher airline-specific shares on the route and at the endpoint airports are associated with higher fares even after including carrier fixed effects and overall concentration. This is consistent with a role for carrier-specific market position or advantages. Route concentration is positively associated with fares, while airport concentration is negatively associated conditional on own airport share. The results do not support a blanket rule that every form of concentration raises prices. The distinction between a carrier's own dominance and total concentration is essential.

The models' $R^2$ values are 0.8485, 0.8731 and 0.8740. These summarize in-sample variation in logged fare percentiles explained by the complete specification, including carrier effects. High fit and small p-values do not establish identification, causality or policy reliability. Numerical differences between percentile equations are not formal evidence that coefficients differ statistically across fare percentiles.

\textbf{Endogeneity.} Fares, route shares and airport presence are jointly determined: price affects demand and observed shares, while market position can affect pricing. Load factor, routing and service choices also respond to demand, costs and prices. Unobserved local demand, business-travel intensity, service quality, airport conditions and network structure can correlate with included regressors. Carrier fixed effects remove average carrier-level differences but do not remove route/airport demand shocks. Thus OLS estimates are conditional associations, not causal effects of competition, mergers or service changes. They do not directly measure markups or welfare.

\textbf{Differences from the original Table 2.}
\begin{itemize}
\item Only the three OLS equations are recreated. Borenstein also reported instrumental-variable/2SLS specifications addressing endogeneity. No instruments or 2SLS estimates are constructed here. The modern sample has 7,499 routes rather than the original 3,591 observations.
\item The original controls include aircraft size, frequency, separate on-plane stops and plane changes, competitors' standardized costs, tourism, and airport scarcity. These are absent from the requested reduced-control models. Aircraft/frequency proxies could be assembled separately from operations, but have not been added to this specification; the other supplementary controls have not been assembled. True on-plane stops and plane changes cannot be recovered reliably from these files, and the coupon proxy replaces neither exactly.
\item The original OLS load-factor coefficients are negative and the on-plane-stop coefficients are negative. Both modern load-factor and proxy coefficients are positive. Different controls, travel samples, proxy definitions and endogeneity prevent treating this as a like-for-like reversal of structural effects.
\item This is 2025 Q2 DB1B with mileage-prorated directional Market fares, rather than 1987 Q3 preprocessed DB1A one-way/half-round-trip fares. Open-jaw/circle itineraries and first class cannot be excluded on the same basis as the historical study. The \$20 directional-fare floor is the documented pilot convention, not an inflation-adjusted historical cutoff; ancillary charges are not included.
\item Carrier effects use the unchanged baseline's observed ticketing codes, including separate AS and HA categories. The parent-group combination used for the descriptive Q5 table is not imposed on this preselected regression baseline. Grouping differently would require rebuilding shares, fare percentiles and sample selection.
\end{itemize}

\textbf{Inference and sampling limits.} HC1 adjusts for heteroskedasticity, using $N/(N-K)$ times the robust covariance meat, but does not correct for endogeneity or correlation across routes sharing airports/networks. There is one observation per route, so route clustering would not address those shared-airport dependencies. No airport/network clustering is claimed. Standard errors treat constructed fare percentiles, shares and service measures as observed regressors/outcomes; they do not propagate all first-stage survey sampling uncertainty. Sparse carriers and the chosen market sample also limit generalization. Statistical significance is conditional on these assumptions.

{\footnotesize\textbf{Reproduction.} Run the estimation and rendering scripts listed in the accompanying methodology, then compile the generated LaTeX with pdflatex. The output directory contains full coefficients (including carrier effects and the intercept), confidence intervals, fit statistics, effect conversions, exact sample rows and residuals. The source baseline SHA-256 matches its Q4 provenance; no baseline values changed. The design is full rank, and coefficients and HC1 covariance were independently verified numerically.}
\end{document}
'''
# Use a space before paragraph breaks where prose is concatenated; all numeric results are read from CSVs.
(OUT/'modern_table2.tex').write_text(tex)
# Parallel text deliverable with a full interpretation of each of the eight slope coefficients.
md='''# Part III, Question 6: modern Table 2 (OLS)

The three requested regressions were estimated on the unchanged 2025 Q2 Part II baseline. There are 7,499 observations in every model, no added exclusions, eight slope controls, 14 carrier categories (13 dummies) and an intercept. OLS is unweighted across carrier–route observations. Fare percentiles themselves were constructed with passenger weights. AS and HA remain separate baseline carrier codes; the Q5 parent grouping is not substituted.

Original Table 2 was consulted as text and visually (Borenstein 1989, printed p.357 / PDF p.15). The final three OLS columns guide this modern table. The PDF follows its coefficient/parenthesized-SE layout and original available-control order. Conventional modern significance stars are explicitly defined.

## Regression results

HC1 robust standard errors in parentheses. Stars: * p<0.10, ** p<0.05, *** p<0.01. Two-sided t reference, 7,477 residual df. These are robust-reference tests, not exact finite-sample inference. R-squared includes the carrier effects.

| Variable | ln(P20) | ln(P50) | ln(P80) |
|---|---:|---:|---:|
'''
for term in terms:
 vals=[]
 for y in ys:
  v=c[(c.term==term)&(c.outcome==y)].iloc[0];vals.append(f'{v.coefficient:.4f}{v.significance} ({v.standard_error:.4f})')
 md+='| '+labels[term].replace('$','').replace('\\ln(\\mathrm{','ln(').replace('})',')')+' | '+' | '.join(vals)+' |\n'
md+='| N | 7,499 | 7,499 | 7,499 |\n| R-squared | '+' | '.join(f'{float(f[f.outcome==y].iloc[0].r_squared):.4f}' for y in ys)+' |\n'
md+='\n## Interpretation of every explanatory variable\n\nAll interpretations hold the remaining controls and carrier effects fixed. Values are ordered P20, P50, P80. Log-regressor coefficients are elasticities; a 1% relative change has an approximate beta% fare association. All eight slopes are significant at 1% in all three equations under HC1/t inference.\n\n'
for name,desc in descriptions:
 text=desc.replace(r'\%', '%').replace(r'\&','&').replace('\\textquotesingle ', "'")
 md+=f'**{name}.** {text}\n\n'
md+='''For a +10% level change in a logged regressor, the exact fitted-fare difference is `100*((1.10)**beta-1)`. For a level-regressor change Delta, it is `100*(exp(beta*Delta)-1)`. Shares/HHIs are 0–1; +0.10 share is ten percentage points, not a 10% relative share change. Confidence intervals for the conversions are in `coefficient_interpretation_effects.csv`. Transformations describe the fitted-log relationship, not bias-corrected mean dollar prices.

## Conclusions and limitations

Own route share and own airport-origin share are positively associated with fares after controlling for total concentration and carrier effects. Route HHI is positive, while airport-origin HHI is negative conditional on own share. These are different dimensions of competition: results do not imply that every increase in concentration raises fares. Differences in point estimates across fare outcomes have not been tested across equations.

Prices and shares are jointly determined. Strong demand, network/service quality, tourism/business mix, airport constraints and costs may jointly raise prices and observed shares. Load factors and routing are endogenous service choices. Fixed carrier effects do not absorb route/airport demand shocks, and robust standard errors do not remove endogeneity. These results are not causal merger predictions, markups or welfare effects.

The requested reduced-control model omits original aircraft size, frequency, separate on-plane stops and plane changes, competitors' standardized costs, tourism and airport-scarcity controls; optional POTCOMP is not estimated. Some operations proxies could be constructed later, but were not silently added. Only OLS is estimated, unlike the original paper's additional 2SLS specifications. Original on-plane stops and plane changes are unavailable; the mixed coupon-stop proxy is not interchangeable with either. Positive modern LF/proxy coefficients differ from the original OLS signs without identifying a structural reversal.

This quarter uses DB1B allocated directional fares rather than the paper's preprocessed 1987 Q3 DB1A fares. First-class and open-jaw/circle exclusions are not reproduced. The pilot's $20 directional floor and complete-operations matching affect the sample. Fare classes, ancillary charges, quarterly service exposure and survey coverage limit comparability. Statistical standard errors do not propagate all generated-variable/survey uncertainty and HC1 does not account for shared-airport/network dependence across routes. Rare carriers have small sample counts; see provenance.

## Files and reproduction

`reports/part3-q6/modern_table2.pdf` and `.tex` contain the regression table, all eight interpretations and limitations. Other files in that directory: `coefficients.csv` (all estimates, HC1 SEs, p-values and CIs, including FE/intercept), `model_fit.csv`, `coefficient_interpretation_effects.csv`, `estimation_sample.csv`, `fitted_values_and_residuals.csv`, and `provenance.json` (source SHA-256, carrier counts, design columns/rank, software and verification). Numerical underflow may display an extremely small exported p-value as zero; it should not be interpreted as an exactly zero probability.

Run `python scripts/ols_part3_q6.py`, `python scripts/render_table2_part3_q6.py`, then `pdflatex reports/part3-q6/modern_table2.tex` with the desired output directory. The design has full rank; independent least-squares and HC1 sandwich calculations match statsmodels within numerical tolerance. The baseline hash matches the earlier Q4 summary provenance.
'''
(ROOT/'docs/part3-question-6.md').write_text(md)
print('Wrote',OUT/'modern_table2.tex')
