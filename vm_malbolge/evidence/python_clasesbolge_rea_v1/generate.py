#!/usr/bin/env python3
"""Encode fixed IN/OUT pairs by the inverse formula from clasesbolge.md."""
import json,pathlib
P=pathlib.Path(__file__).resolve().parent
OPS=[23,5]*4+[81];VALID={4,5,23,39,40,62,68,81}
def encode(op,pos):return 33+((op-pos-33)%94)
def build(ops):return bytes(encode(op,i) for i,op in enumerate(ops))
main=build(OPS);mut=list(OPS);mut[1]=68;control=build(mut)
for image,ops in ((main,OPS),(control,mut)):
 assert all(33<=v<=126 and (v+i)%94==ops[i] and ops[i] in VALID for i,v in enumerate(image))
(P/'echo4.mb').write_bytes(main);(P/'ctrl_no_first_out.mb').write_bytes(control)
r={'ops':OPS,'source_hex':main.hex(),'source_ascii':main.decode('ascii'),'control_ops':mut,'control_ascii':control.decode('ascii'),'formula':'33+((op-c-33)%94)'}
(P/'encoding.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
