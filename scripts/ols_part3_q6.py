"""Part III Q6: unweighted OLS of baseline fare percentiles, carrier FE, HC1 inference."""
from pathlib import Path
import hashlib,json,platform
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import statsmodels
import statsmodels.api as sm
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/part3-q6';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'data/processed/2025Q2/q4_baseline_one_carrier_per_route.csv'
raw=SOURCE.read_bytes();source_hash=hashlib.sha256(raw).hexdigest();d=pd.read_csv(SOURCE)
xcols=['ln_Distance','ln_LoadFactor','ln_Circuity','Stops_coupon_proxy','OrgShare','OrgHerf','RouteShare','RouteHerf']
ys=['ln_P20','ln_P50','ln_P80']
assert len(d)==7499 and not d.duplicated(['a','b']).any()
assert d.eligible.all() and d.Year.eq(2025).all() and d.Quarter.eq(2).all()
assert d.Stops_on_plane.isna().all()
for level,logged in [('P20','ln_P20'),('P50','ln_P50'),('P80','ln_P80'),('Distance','ln_Distance'),('LoadFactor','ln_LoadFactor'),('Circuity','ln_Circuity')]:
 assert d[level].gt(0).all();np.testing.assert_allclose(np.log(d[level]),d[logged],rtol=1e-12,atol=1e-12)
# One common complete-case sample, limited strictly to modeled outcomes/controls/carrier.
mask=d[xcols+ys].notna().all(axis=1)&d.carrier_fe.notna()
mask &= np.isfinite(d[xcols+ys]).all(axis=1)
sample=d.loc[mask].copy()
assert len(sample)==7499
assert sample.carrier_fe.eq(sample.carrier).all()
carriers=sorted(sample.carrier_fe.unique());reference=carriers[0]
fe=pd.get_dummies(pd.Categorical(sample.carrier_fe,categories=carriers),prefix='carrier',drop_first=True,dtype=float)
fe.index=sample.index
X=sm.add_constant(pd.concat([sample[xcols].astype(float),fe],axis=1),has_constant='add')
assert np.linalg.matrix_rank(X.to_numpy())==X.shape[1]
n,k=X.shape;xx=X.to_numpy();bread=np.linalg.inv(xx.T@xx)
rows=[];effectrows=[];fits=[];verify={}
models={}
for outcome in ys:
 model=sm.OLS(sample[outcome],X,missing='raise').fit(cov_type='HC1',use_t=True)
 models[outcome]=model
 # Independent coefficient and HC1 sandwich calculation to verify library results.
 beta,_,rank,_=np.linalg.lstsq(xx,sample[outcome].to_numpy(),rcond=None)
 resid=sample[outcome].to_numpy()-xx@beta
 manual_cov=n/(n-k)*bread@((xx*resid[:,None]).T@(xx*resid[:,None]))@bread
 np.testing.assert_allclose(model.params,beta,rtol=1e-9,atol=1e-10)
 np.testing.assert_allclose(model.cov_params(),manual_cov,rtol=1e-7,atol=1e-9)
 assert np.abs(xx.T@resid).max()<1e-6
 assert int(model.nobs)==7499 and np.isfinite(model.bse).all() and (model.bse>0).all()
 ci=model.conf_int(alpha=.05)
 for term in X.columns:
  b=float(model.params[term]);se=float(model.bse[term]);p=float(model.pvalues[term]);lo=float(ci.loc[term,0]);hi=float(ci.loc[term,1])
  star='***' if p<.01 else '**' if p<.05 else '*' if p<.10 else ''
  rows.append(dict(outcome=outcome,term=term,coefficient=b,standard_error=se,t_stat=float(model.tvalues[term]),p_value=p,ci95_lower=lo,ci95_upper=hi,significance=star))
  if term in xcols:
   if term.startswith('ln_'):
    change=np.log(1.1);description='10% relative increase in level regressor'
   elif term=='Stops_coupon_proxy':
    change=1.0;description='One-unit increase in average coupon-stop proxy'
   else:
    change=.1;description='0.10 increase on 0-1 scale (10 percentage points for shares)'
   effectrows.append(dict(outcome=outcome,term=term,change_in_regressor=change,scenario=description,percent_fare_difference=100*np.expm1(b*change),ci95_lower=100*np.expm1(lo*change),ci95_upper=100*np.expm1(hi*change),p_value=p))
 fits.append(dict(outcome=outcome,n=int(model.nobs),r_squared=float(model.rsquared),adjusted_r_squared=float(model.rsquared_adj),df_resid=int(model.df_resid),parameters=k,carrier_categories=len(carriers),carrier_dummy_variables=len(carriers)-1,covariance='HC1',p_value_distribution='t with N-K degrees of freedom',weighting='Unweighted OLS'))
 verify[outcome]={'max_abs_coefficient_difference':float(np.abs(model.params-beta).max()),'max_abs_covariance_difference':float(np.abs(model.cov_params().to_numpy()-manual_cov).max()),'max_abs_normal_equations_error':float(np.abs(xx.T@resid).max())}
 sample[outcome+'_fitted']=model.fittedvalues
 sample[outcome+'_residual']=model.resid
coef=pd.DataFrame(rows);coef.to_csv(OUT/'coefficients.csv',index=False,float_format='%.15g')
pd.DataFrame(effectrows).to_csv(OUT/'coefficient_interpretation_effects.csv',index=False,float_format='%.15g')
pd.DataFrame(fits).to_csv(OUT/'model_fit.csv',index=False,float_format='%.15g')
sample[['Year','Quarter','a','b','carrier',*xcols,*ys]].to_csv(OUT/'estimation_sample.csv',index=False,float_format='%.15g')
sample[['Year','Quarter','a','b','carrier',*[x+suffix for x in ys for suffix in ['_fitted','_residual']]]].to_csv(OUT/'fitted_values_and_residuals.csv',index=False,float_format='%.15g')
source_q4=ROOT/'reports/part3-q4/summary_provenance.json'
prior=json.loads(source_q4.read_text()) if source_q4.exists() else {}
if prior:assert prior['source_sha256']==source_hash
provenance=dict(source=str(SOURCE.relative_to(ROOT)),source_sha256=source_hash,unchanged_from_q4_summary=prior.get('source_sha256')==source_hash,baseline_rows=len(d),estimation_rows=n,dropped_rows=len(d)-n,all_model_variables_complete=bool(mask.all()),carrier_counts={str(k):int(v) for k,v in sample.carrier_fe.value_counts().sort_index().items()},reference_carrier=reference,design_columns=list(X.columns),rank=int(np.linalg.matrix_rank(xx)),condition_number=float(np.linalg.cond(xx)),standard_errors='HC1 heteroskedasticity robust; no clustering',p_values='Two-sided t reference distribution with N-K degrees of freedom',models=fits,numerical_verification=verify,software={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'pandas':pd.__version__,'statsmodels':statsmodels.__version__},original_reference='Borenstein (1989), Table 2, printed p.357 / PDF p.15; OLS columns only',parent_grouping='Unchanged baseline ticketing-carrier codes; AS and HA are separate as in Part II, not the grouped Q5 descriptive table',regressions_run='Only the three requested OLS models; no 2SLS or quantile regressions')
(OUT/'provenance.json').write_text(json.dumps(provenance,indent=2,allow_nan=False)+'\n')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
print(coef[coef.term.isin(xcols)].pivot(index='term',columns='outcome',values='coefficient').to_string())
print(coef[coef.term.isin(xcols)][['outcome','term','standard_error','p_value','significance']].to_string(index=False))
print(pd.DataFrame(fits).to_string(index=False));print('Carriers',carriers);print('Numerical verification',verify)
