#!/usr/bin/env python3
"""Increment each input byte modulo 256, stopping at EOF."""
import sys
while True:
    data = sys.stdin.buffer.read(4096)
    if not data:
        break
    sys.stdout.buffer.write(bytes((byte + 1) & 255 for byte in data))
