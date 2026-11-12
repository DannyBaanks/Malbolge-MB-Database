#!/usr/bin/env python3
"""Check the literal disjoint per-cell G5 design, not all possible designs."""
import collections,json,pathlib,z3
P=pathlib.Path(__file__).resolve().parent
island='j*jpojpooj*ojpooooi';counts=dict(collections.Counter(island));cost=len(island)
assert cost==19 and counts=={'j':5,'*':2,'p':3,'o':8,'i':1}
# Literal assumptions: a distinct disjoint 19-code-cell island per target;
# R restores every code cell of R2 and B; R2 restores every code cell of R.
r,s,b=z3.Ints('r s b');solver=z3.Solver();solver.set(unsat_core=True)
for name,expr in [('positive_body',b>=1),('nonnegative_r',r>=0),('nonnegative_s',s>=0),
                  ('r_islands',r>=cost*(s+b)),('r2_islands',s>=cost*r)]:solver.assert_and_track(expr,name)
status=str(solver.check());core=sorted(map(str,solver.unsat_core()));assert status=='unsat'
# Sharing can satisfy simple cardinality, but gives no runnable implementation.
shared=z3.Solver();shared.add(r==19,s==19,b==2);shared_status=str(shared.check());assert shared_status=='sat'
z={'island_length':cost,'island_op_counts':counts,'literal_constraints':['b>=1','r>=0','s>=0','r>=19*(s+b)','s>=19*r'],
   'status':status,'unsat_core':core,'derived':'r >= 19*(19*r+b) = 361*r+19*b',
   'shared_schematic_only':{'r':19,'s':19,'b':2,'arithmetic_status':shared_status,'runtime_claim':'NOT_DEMONSTRATED'},
   'scope':'disjoint dedicated 19-cell islands which restore every code cell; does not rule out shared reusable routines, semantic phase-tolerant NOPs, or block-level restoration'}
(P/'architecture.results.json').write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True))
