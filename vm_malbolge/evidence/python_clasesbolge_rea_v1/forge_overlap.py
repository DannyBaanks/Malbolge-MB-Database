#!/usr/bin/env python3
"""Compare UNIECO's desired changed addresses to Forge's fixed low scratch area."""
import hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
state=ROOT/'vm_malbolge/evidence/unieco_v1/state_bridge_v2.results.json';src=ROOT.parent/'BolgeForge/tools/resynthesize.py'
items=json.loads(state.read_text())['changes'];targets={x['cell'] for x in items};low=set(range(30,99));specific={33,35,36,48,50,51,71,73,74,82,94}
r={'state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),'forge_source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'target_count':len(targets),'forge_low_area_half_open':[30,99],'overlap_low':sorted(targets&low),'overlap_low_count':len(targets&low),'named_scratch_and_control_addresses':sorted(specific),'overlap_named':sorted(targets&specific),'scope':'address overlap means scheduler/lifetimes need reconciliation; does not prove conflict is fatal or that Forge can schedule UNIECO'}
(P/'forge_overlap.results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
