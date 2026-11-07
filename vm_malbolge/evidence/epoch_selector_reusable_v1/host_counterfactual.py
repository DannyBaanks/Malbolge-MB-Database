import sys
from pathlib import Path
sys.path.insert(0,'tools');import oracle_classic as o
src=Path('vm_malbolge/evidence/epoch_selector_rearm_v0/rearmed2.mb').read_text('latin1')

def run(mode):
 m=o.load_memory(src);a=c=d=idx=0;data=[1,2,1];first=None;outs=[];changed=[];patches=[]
 for step in range(1,300001):
  if not 33<=m[c]<=126:return bytes(outs),step,'NONPRINTABLE',changed,patches
  op=(m[c]+c)%94
  if op==4:c=m[d]
  elif op==5:outs.append(a%256)
  elif op==23:
   if idx==0:first=m.copy()
   if idx==1 or (idx>1 and mode=='periodic_all'):
    changed=[i for i in range(59049) if m[i]!=first[i]]
    choose={'none':[],'flag':[58908],'carry':[59047],'both':[58908,59047],'all':changed,'periodic_all':changed}[mode]
    for i in choose:
     if m[i]!=first[i]:patches.append((i,m[i],first[i]));m[i]=first[i]
   if idx>=len(data):return bytes(outs),step,'EOF',changed,patches
   a=data[idx];idx+=1
  elif op==39:m[d]=m[d]//3+(m[d]%3)*19683;a=m[d]
  elif op==40:d=m[d]
  elif op==62:m[d]=o.crazy_op(a,m[d]);a=m[d]
  elif op==81:return bytes(outs),step,'HALT',changed,patches
  if 33<=m[c]<=126:m[c]=o._ENC[m[c]]
  c=(c+1)%59049;d=(d+1)%59049
 return bytes(outs),300000,'BUDGET',changed,patches
for mode in ['none','flag','carry','both','all','periodic_all']:
 out,steps,status,changed,patches=run(mode);print(mode,'output',out.hex(),'steps',steps,'status',status,'changed=',len(changed),'patches=',len(patches),'first',patches[:12]);
 if mode=='all':print('changed sample',changed[:100])
