#!/usr/bin/env python3
"""Characterize the four-CRAZY clock route; no extra native claim."""
import importlib.util,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);f=m.SE.crazy;ONE=29524;N=59049

def route(x,ctrl):
 e=f(ONE,x);reset=f(e,e);q=f(ctrl,reset);return f(q,q)

bad=[x for x in range(N) if route(x,40)!=40]
# Each diagonal result has per-trit image {0,1}; enumerate all words.
def digits(w):
 return [(w//(3**i))%3 for i in range(10)]
all_targets=[w for w in range(N) if 2 not in digits(w)]
examples=[0,1,40,ONE];tested=0
for want in all_targets:
 q=ONE-want;ctrl=f(q,ONE)
 for x in [0,1,70,ONE,59048]:
  assert route(x,ctrl)==want;tested+=1
assert not bad and len(all_targets)==1024
report={'orientation':'crazy(accumulator,cell)=table[cell][accumulator]','fixed_target':40,
        'initial_words_tested':N,'fixed_target_mismatches':len(bad),
        'diagonal_per_trit_values':sorted({f(v,v)%3 for v in range(3)}),
        'diagonal_representable_word_count':len(all_targets),'generalization_sample_pairs':tested,
        'examples':examples,'scope':'host-side algebra; native image implements one fixed target and driver, not 1024 targets or a reusable scheduler'}
(P/'algebra_scope.results.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
