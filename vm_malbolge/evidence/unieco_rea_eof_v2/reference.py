#!/usr/bin/env python3
"""Reference byte-for-byte cat; binary input and output, EOF terminates."""
import sys

while True:
    chunk = sys.stdin.buffer.read(4096)
    if not chunk:
        break
    sys.stdout.buffer.write(chunk)
