"""Read-only aggregate comparison of two existing local LGD research methods."""
import hashlib
import json
import math
import os
from pathlib import Path

ROOT=Path(os.environ.get('LGD_REPORT_ROOT',str(Path(__file__).resolve().parent/'data'/'private-lgd')))
FILES=('lgd-signed-research-v0.1.0/report.json','lgd-signed-hurdle-v0.1.1/report.json')

def compare_existing_lgd(root=ROOT):
    reports=[]
    provenance=[]
    for relative in FILES:
        path=Path(root)/relative
        body=path.read_bytes()
        reports.append(json.loads(body))
        provenance.append({'artifact':relative,'sha256':hashlib.sha256(body).hexdigest()})
    ridge,hurdle=reports
    outcome=ridge['outcome_version']
    if outcome not in hurdle['target']:
        raise ValueError('Comparison blocked: outcome versions differ')
    metrics=hurdle['pooled_comparison']
    names=('ridge_loss_sharing','signed_hurdle')
    methods=[]
    for key in names:
        m=metrics[key]
        if not isinstance(m['cases'],int) or m['cases']<=0 or any(not math.isfinite(m[x]) or m[x]<0 for x in ('mae','rmse')):
            raise ValueError('Comparison blocked: invalid aggregate metrics')
        methods.append({'id':key,'name':'Ridge regression with loss-sharing features' if key==names[0] else 'Signed hurdle model','description':'Regularized regression estimates the signed loss ratio directly.' if key==names[0] else 'Separates zero/nonzero loss, positive/negative sign and conditional loss/gain magnitudes.',**{k:m[k] for k in ('cases','mae','rmse')}})
    if methods[0]['cases']!=methods[1]['cases']:
        raise ValueError('Comparison blocked: reported evaluation counts differ')
    delta=methods[1]['mae']-methods[0]['mae']
    return {'tool':'lgd_compare','mode':'existing_research_report_comparison_no_refit_no_llm','population':'Fannie Mae multifamily, 2026Q1 snapshot','outcome':ridge['target'],'outcome_version':outcome,'methods':methods,'evaluation':'Pooled historical backtests in the signed-hurdle report; matching reported case counts. Row-level prediction pairing has not been independently rechecked by this agent.', 'checks':[{'name':'Shared outcome version in both reports','passed':True},{'name':'Matching reported evaluation counts','passed':True},{'name':'Finite nonnegative reported errors','passed':True}], 'mae_difference_hurdle_minus_ridge':delta,'interpretation':f'Ridge has lower reported pooled MAE by {abs(delta):.4f} ratio units.' if delta>0 else 'The signed hurdle model has no higher reported pooled MAE.','provenance':provenance,'limitations':hurdle['limitations']+['Source ratio is not discounted economic workout LGD. Negative ratios remain visible; no clipping to zero.','Comparison reads existing aggregate metrics only; it does not fit, validate or approve a model.','No loan-level data or serialized model objects are loaded or transmitted to an AI provider.']}
