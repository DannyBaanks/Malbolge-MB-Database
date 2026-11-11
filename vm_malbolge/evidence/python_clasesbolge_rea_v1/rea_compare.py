#!/usr/bin/env python3
import json,pathlib
P=pathlib.Path(__file__).resolve().parent
def get(name):return json.loads((P/('rea_'+name+'.redacted.json')).read_text())
def process(name):
 r=get(name)['normalized_result']; s=''.join(x['data'] for x in r['frames']).strip()
 return {'hex':s,'exit':r['exit']}
py=process('python4');bf=process('bf4');pyshort=process('python_short');bfshort=process('bf_short')
mal=get('malbolge4')['normalized_result'];ctl=get('malbolge_control')['normalized_result'];err=get('malbolge_short')
checks={'python_bf_malbolge_same':py['hex']==bf['hex']==bytes(mal['output_bytes']).hex()=='41623921','python_bf_exit':py['exit']['code']==bf['exit']['code']==0,'malbolge_halted':mal['run']['status']=='HALTED' and mal['run']['steps']==9,'control_distinct':bytes(ctl['output_bytes']).hex()=='623921','short_python_bf_differ':pyshort['hex']=='416239' and bfshort['hex']=='41623900','rea_short_is_tool_error':err.get('isError') is True}
r={'checks':checks,'all_checks':all(checks.values()),'python_four':py,'bf_four':bf,'malbolge_four_output_hex':bytes(mal['output_bytes']).hex(),'malbolge_four_status':mal['run']['status'],'control_output_hex':bytes(ctl['output_bytes']).hex(),'python_short':pyshort,'bf_short':bfshort,'rea_short_error':err,'limitations':'REA Python and BF observations are process-level wrappers that print hex; Malbolge is a bounded in-process replay; none is an electrical or transistor trace.'}
(P/'rea_compare.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['all_checks']
