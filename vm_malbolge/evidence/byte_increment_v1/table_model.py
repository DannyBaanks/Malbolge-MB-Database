#!/usr/bin/env python3
"""Study a table-index and rearm design; not an executable Malbolge loop."""
import hashlib
import importlib.util
import json
import pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
s=importlib.util.spec_from_file_location('compose',ROOT/'vm_malbolge/evidence/epoch_dload_compose_v1/probe.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
crazy=m.SE.crazy;rot=m.SE.rot;N=59049;base=47*729
# On positions 0..5, row 1 twice is the identity on all three trits.
# Above position 5 every byte has zero; choose rows taking 0 to the base trit.
table=((1,0,0),(1,0,2),(2,2,1));trits=lambda n:[(n//(3**i))%3 for i in range(10)]
r1=[1]*6;r2=[1]*6
for target in trits(base)[6:]:
    pairs=[(x,y) for x in range(3) for y in range(3) if table[y][table[x][0]]==target]
    assert pairs
    x,y=pairs[0];r1.append(x);r2.append(y)
mask1=sum(x*3**i for i,x in enumerate(r1));mask2=sum(x*3**i for i,x in enumerate(r2))
def index(b):return crazy(crazy(b,mask1),mask2)
def rol(v):
    for _ in range(9):v=rot(v)
    return v
entries=[rol((b+1)%256) for b in range(256)]
values=[index(b) for b in range(256)]; assert values==[base+b for b in range(256)]
# Malbolge MOVD increments d after reading the stored pointer: table lives at index+1.
lookup_addresses=[v+1 for v in values]
read=[];restored=[]
for b,cell in enumerate(entries):
    original=cell;cell=rot(cell);read.append(cell%256)
    for _ in range(9):cell=rot(cell)
    restored.append(cell==original)
expected=[(b+1)%256 for b in range(256)]
control=[rot(entries[b])%256 for b in range(256)] # negative: use wrong index
wrong=[control[(b+1)%256] for b in range(256)]
result={'orientation':'crazy(accumulator,cell) = table[cell][accumulator]',
        'index_base':base,'mask1':mask1,'mask2':mask2,'mask1_trits':r1,'mask2_trits':r2,
        'all_indices_equal_base_plus_byte':values==[base+b for b in range(256)],
        'lookup_min':min(lookup_addresses),'lookup_max':max(lookup_addresses),
        'rotated_table_matches_increment':read==expected,'ten_rotations_restore_table':all(restored),
        'wrong_index_control_mismatches':sum(a!=b for a,b in zip(wrong,expected)),
        'examples':{str(b):{'index':values[b],'lookup_address':lookup_addresses[b],'table_initial':entries[b],
                            'after_first_rot':rot(entries[b]),'output_byte':read[b]} for b in [0,1,127,254,255]},
        'table_sha256':hashlib.sha256(json.dumps(entries,separators=(',',':')).encode()).hexdigest(),
        'scope':'pure word arithmetic and abstract memory layout only; masks consumed by CRAZY; no control flow, mask rearm, loader or native program demonstrated'}
(P/'table_model.results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
assert result['all_indices_equal_base_plus_byte'] and result['rotated_table_matches_increment'] and result['ten_rotations_restore_table'] and result['wrong_index_control_mismatches']==256
