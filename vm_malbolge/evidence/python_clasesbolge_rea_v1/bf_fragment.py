#!/usr/bin/env python3
"""Binary BF fragment ,.; EOF=0. Only complete repeated pairs are accepted."""
import io,sys

def check(source):
    if not source or len(source)%2 or any(source[i:i+2]!=',.' for i in range(0,len(source),2)):
        raise ValueError('only one or more consecutive ,. pairs are supported')

def execute(source,data):
    check(source);out=bytearray();pos=0
    for _ in range(len(source)//2):
        v=data[pos] if pos<len(data) else 0
        if pos<len(data):pos+=1
        out.append(v)
    return bytes(out)

def compile_fragment(source):
    check(source);ops=[x for _ in range(len(source)//2) for x in (23,5)]+[81]
    return bytes(33+((op-i-33)%94) for i,op in enumerate(ops))

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--hex':
        print(execute(',.,.,.,.',bytes.fromhex(sys.argv[2])).hex());return
    sys.stdout.buffer.write(execute(',.,.,.,.',sys.stdin.buffer.read()))
if __name__=='__main__':main()
