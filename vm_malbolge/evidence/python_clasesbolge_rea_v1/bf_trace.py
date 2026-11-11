#!/usr/bin/env python3
"""Per-command observations for the restricted BF echo fragment."""
import importlib.util,json,pathlib,sys
P=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('bf_fragment',P/'bf_fragment.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
source=(P/'echo4.bf').read_text().strip();m.check(source);data=bytes.fromhex(sys.argv[1]);cell=0;at=0;out=bytearray();events=[]
for pc,op in enumerate(source):
 before=cell
 if op==',':
  if at<len(data):cell=data[at];at+=1
  else:cell=0
 else:out.append(cell)
 events.append({'pc':pc,'op':op,'cell_before':before,'cell_after':cell,'input_consumed':at,'output_hex':out.hex()})
assert bytes(out)==m.execute(source,data)
print(json.dumps({'program':source,'input_hex':data.hex(),'output_hex':out.hex(),'events':events},separators=(',',':')))
