#!/usr/bin/env python3
"""Compare REA Malbolge replay with scratch and with native GDB stores."""
import json,pathlib,re
P=pathlib.Path(__file__).resolve().parent
rea=json.loads((P/'unieco_rea_trace.redacted.json').read_text())['normalized_result']
scratch=json.loads((P/'multi_prepare_v2.results.json').read_text())['cases']['main']
native=json.loads((P/'unieco_rea_gdb4.redacted.json').read_text())['normalized_result']
static=json.loads((P/'unieco_rea_native_write.redacted.json').read_text())['normalized_result']
events=[(e['step'],e['position'],e['opcode'],e['d']) for e in rea['events']]
other=[(e['step'],e['pc'],e['op'],e['d']) for e in scratch['trace']]
text=''.join(f['data'] for f in native['frames'])
before=[tuple(map(int,x)) for x in re.findall(r'BEFORE cell=(\d+) old=(\d+) pending=(\d+)',text)]
after=[tuple(map(int,x)) for x in re.findall(r'AFTER cell=(\d+) actual=(\d+)',text)]
changes=[(w['position'],w['value_before'],w['value_after']) for e in rea['events'] if e['opcode']==62 for w in e['writes'] if w['position'] in (47,64,123)]
checks={'rea_halt':rea['run']['status']=='HALTED','no_truncation':not rea['run']['events_truncated'],'trace_matches_scratch':events==other,'native_exited':native['exit']['reason']=='exited' and native['exit']['code']==0,'native_before_matches_replay':before==changes,'native_after_matches_replay':after==[(i,v) for i,_,v in changes],'native_static_store':'0x00001486' in static['stdout'] and 'mov   word [rdx], ax' in static['stdout']}
r={'checks':checks,'all_checks':all(checks.values()),'native_before':before,'native_after':after,'rea_crazy_writes':changes,'matched_steps':len(events),'limitations':'selected CRAZY stores only; native GDB breakpoint perturbs execution and observes process state, not electrical transistor-level behavior; REA replay is in-process semantics'}
(P/'rea_compare.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['all_checks']
