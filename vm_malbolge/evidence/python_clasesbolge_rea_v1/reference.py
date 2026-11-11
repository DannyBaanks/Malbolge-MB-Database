#!/usr/bin/env python3
"""Copy at most four bytes, stopping early at EOF."""
import io,sys

def echo4(source,destination):
    for _ in range(4):
        byte=source.read(1)
        if not byte:break
        destination.write(byte)

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--hex':
        dest=io.BytesIO();echo4(io.BytesIO(bytes.fromhex(sys.argv[2])),dest)
        print(dest.getvalue().hex());return
    echo4(sys.stdin.buffer,sys.stdout.buffer)

if __name__=='__main__':main()
