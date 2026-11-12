#!/usr/bin/env python3
"""Bounded native streaming check; the harness stops the program after EOF output."""
import hashlib
import json
import os
import pathlib
import select
import subprocess
import sys
import tempfile
import time
P=pathlib.Path(__file__).resolve().parent
root=P.parents[2]
image=pathlib.Path(sys.argv[1])/'positive.mb'
data=bytes((73*i+195)%256 for i in range(10000))
with tempfile.TemporaryFile() as source:
    source.write(data); source.seek(0)
    proc=subprocess.Popen(['stdbuf','-o0',str(root.parent/'Malbolge-PureEpoch/build/olmstead'),str(image)],stdin=source,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output=bytearray(); deadline=time.monotonic()+30
    while len(output)<len(data)+1 and time.monotonic()<deadline:
        ready,_,_=select.select([proc.stdout],[],[],max(0,deadline-time.monotonic()))
        if not ready: break
        chunk=os.read(proc.stdout.fileno(),min(16384,len(data)+1-len(output)))
        if not chunk: break
        output.extend(chunk)
    proc.terminate()
    try: proc.wait(timeout=2)
    except subprocess.TimeoutExpired: proc.kill();proc.wait(timeout=2)
    result={'bytes_in':len(data),'prefix_bytes':len(output),'input_sha256':hashlib.sha256(data).hexdigest(),'output_prefix_sha256':hashlib.sha256(output[:len(data)]).hexdigest(),'first_10000_match':output[:len(data)]==data,'extra_eof_byte_hex':bytes(output[len(data):]).hex(),'terminated_by_harness':True,'native_rc':proc.returncode}
    print(json.dumps(result,indent=2))
    assert result['first_10000_match'] and result['extra_eof_byte_hex']=='a8'
