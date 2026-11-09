"""
Pure Python MD4 fallback for OpenSSL 3.0+ / Python 3.10+ environments.
Fixes 'unsupported hash type MD4' error during Active Directory NTLM authentication.
"""

import hashlib
import struct


class PureMD4:
    """RFC 1320 MD4 implementation in pure Python."""

    def __init__(self, data=b""):
        self.remainder = b""
        self.count = 0
        self.h = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476]
        if data:
            self.update(data)

    def update(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")

        def F(x, y, z): return (x & y) | (~x & z)
        def G(x, y, z): return (x & y) | (x & z) | (y & z)
        def H(x, y, z): return x ^ y ^ z
        def lrot(x, n): return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

        message = self.remainder + data
        self.count += len(data)
        num_blocks = len(message) // 64
        for i in range(num_blocks):
            block = message[i * 64 : (i + 1) * 64]
            X = struct.unpack("<16I", block)
            A, B, C, D = self.h
            for j, s in zip(range(16), [3, 7, 11, 19] * 4):
                A = lrot((A + F(B, C, D) + X[j]) & 0xFFFFFFFF, s)
                A, B, C, D = D, A, B, C
            for j, s in zip([0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15], [3, 5, 9, 13] * 4):
                A = lrot((A + G(B, C, D) + X[j] + 0x5A827999) & 0xFFFFFFFF, s)
                A, B, C, D = D, A, B, C
            for j, s in zip([0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15], [3, 9, 11, 15] * 4):
                A = lrot((A + H(B, C, D) + X[j] + 0x6ED9EBA1) & 0xFFFFFFFF, s)
                A, B, C, D = D, A, B, C
            self.h[0] = (self.h[0] + A) & 0xFFFFFFFF
            self.h[1] = (self.h[1] + B) & 0xFFFFFFFF
            self.h[2] = (self.h[2] + C) & 0xFFFFFFFF
            self.h[3] = (self.h[3] + D) & 0xFFFFFFFF
        self.remainder = message[num_blocks * 64 :]

    def digest(self):
        def F(x, y, z): return (x & y) | (~x & z)
        def G(x, y, z): return (x & y) | (x & z) | (y & z)
        def H(x, y, z): return x ^ y ^ z
        def lrot(x, n): return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

        orig_len = self.count * 8
        message = self.remainder + b"\x80"
        message += b"\x00" * ((56 - (len(message) % 64)) % 64)
        message += struct.pack("<Q", orig_len)

        A, B, C, D = list(self.h)
        for i in range(0, len(message), 64):
            X = struct.unpack("<16I", message[i : i + 64])
            AA, BB, CC, DD = A, B, C, D
            for j, s in zip(range(16), [3, 7, 11, 19] * 4):
                A = lrot((A + F(B, C, D) + X[j]) & 0xFFFFFFFF, s)
                A, B, C, D = D, A, B, C
            for j, s in zip([0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15], [3, 5, 9, 13] * 4):
                A = lrot((A + G(B, C, D) + X[j] + 0x5A827999) & 0xFFFFFFFF, s)
                A, B, C, D = D, A, B, C
            for j, s in zip([0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15], [3, 9, 11, 15] * 4):
                A = lrot((A + H(B, C, D) + X[j] + 0x6ED9EBA1) & 0xFFFFFFFF, s)
                A, B, C, D = D, A, B, C
            A = (A + AA) & 0xFFFFFFFF
            B = (B + BB) & 0xFFFFFFFF
            C = (C + CC) & 0xFFFFFFFF
            D = (D + DD) & 0xFFFFFFFF
        return struct.pack("<4I", A, B, C, D)

    def hexdigest(self):
        return self.digest().hex()


def apply_md4_patch():
    """Ensure hashlib.new('md4') works even if OpenSSL disabled MD4."""
    try:
        hashlib.new("md4", b"test")
    except (ValueError, Exception):
        _orig_new = hashlib.new

        def _patched_new(name, data=b"", **kwargs):
            if name.lower() == "md4":
                return PureMD4(data)
            return _orig_new(name, data, **kwargs)

        hashlib.new = _patched_new
