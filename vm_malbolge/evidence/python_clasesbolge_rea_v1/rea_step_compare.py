#!/usr/bin/env python3
import json,pathlib
P=pathlib.Path(__file__).resolve().parent
b=json.loads((P/'rea_bf_trace.redacted.json').read_text())['normalized_result']
txt=''.join(f['data'] for f in b['frames']).strip(); bf=json.loads(txt)
m=json.loads((P/'rea_malbolge4.redacted.json').read_text())['normalized_result'];events=m['events'];rows=[]
for i in range(4):
 bi,bo=bf['events'][2*i:2*i+2];mi,mo=events[2*i:2*i+2]
 rows.append({'pair':i,'bf_input_pc':bi['pc'],'bf_cell_after_input':bi['cell_after'],'bf_out_pc':bo['pc'],'malbolge_in_pc':mi['position'],'malbolge_out_pc':mo['position'],'malbolge_a_before_out':mo['a'],'same_byte':bi['cell_after']==bo['cell_before']==mo['a'],'opcode_pair_matches':(mi['opcode'],mo['opcode'])==(23,5)})
checks={'four_pairs':len(rows)==4,'bf_capture_exit_0':b['exit']['code']==0,'malbolge_halts':m['run']['status']=='HALTED','all_values_match':all(x['same_byte'] and x['opcode_pair_matches'] for x in rows),'outputs_match':bf['output_hex']==bytes(m['output_bytes']).hex()=='41623921'}
r={'checks':checks,'all_checks':all(checks.values()),'pairs':rows,'scope':'one ASCII input, BF tracer is an explicit restricted interpreter captured as a process; REA Malbolge trace is in-process replay; no arbitrary programs or EOF equivalence'}
(P/'rea_step_compare.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['all_checks']
