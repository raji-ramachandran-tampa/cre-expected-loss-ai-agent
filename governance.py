"""Shared governance boundary used by actual tool execution and demonstrations."""
import hashlib
import json
import math
from pathlib import Path

PATH=Path(__file__).resolve().parent/'governance-policy.json'

class PolicyDenied(ValueError):
    pass

def policy():
    body=PATH.read_bytes()
    return {**json.loads(body),'sha256':hashlib.sha256(body).hexdigest()}

def tool_decision(name,args):
    p=policy()
    if name not in p['allowed_tools']:
        return {'allowed':False,'rule':'approved_tools','reason':'Tool is not on the approved list. Approval, source edits and lending decisions are outside the agent role.','policy_version':p['version']}
    if name=='ead' and (not isinstance(args,dict) or set(args)!={'case_id'} or args.get('case_id') not in p['allowed_case_ids']):
        return {'allowed':False,'rule':'synthetic_inputs','reason':'Only registered synthetic cases are permitted; arbitrary borrower inputs are blocked.','policy_version':p['version']}
    if name=='evidence' and args!={}:
        return {'allowed':False,'rule':'evidence_scope','reason':'Evidence tool cannot access arbitrary paths.','policy_version':p['version']}
    if name=='lgd_compare' and args!={'comparison_id':'signed_lgd_research_2026Q1'}:
        return {'allowed':False,'rule':'registered_lgd_reports','reason':'Only the registered aggregate research comparison is permitted; arbitrary files or loan records are blocked.','policy_version':p['version']}
    return {'allowed':True,'rule':'approved_tool_contract','reason':'Registered tool and permitted input contract.','policy_version':p['version']}

def require_memory(ttl):
    if not isinstance(ttl,(int,float)) or not math.isfinite(ttl) or not 0<ttl<=policy()['max_memory_ttl_seconds']:
        raise PolicyDenied('Memory expiration must be finite and no longer than 24 hours.')

def require_provider(provider):
    if provider!='offline' and not policy()['live_provider_enabled']:
        raise PolicyDenied('Live AI access is disabled by the local policy. The operator must authorize provider access before enabling it.')
