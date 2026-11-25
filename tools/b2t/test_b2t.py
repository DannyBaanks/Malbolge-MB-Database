from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

import b2t


class TestRoundtrip(unittest.TestCase):
    def assert_roundtrip(self, data: bytes) -> None:
        encoded = b2t.encode_bytes(data)
        self.assertEqual(encoded.data, data)
        self.assertEqual(b2t.decode_container(encoded.container), data)

    def test_empty_input_roundtrip(self) -> None:
        self.assert_roundtrip(b"")

    def test_single_byte_roundtrip(self) -> None:
        for value in range(256):
            self.assert_roundtrip(bytes([value]))

    def test_several_lengths_roundtrip(self) -> None:
        for length in (0, 1, 2, 3, 5, 8, 15, 16, 31, 32, 33, 64, 100):
            data = bytes((index * 31 + 7) % 256 for index in range(length))
            self.assert_roundtrip(data)

    def test_payload_stays_below_reserved_range(self) -> None:
        for word in b2t.encode_bytes(b"\xff" * 16).words:
            self.assertLess(word, 32768)


class TestBitPacking(unittest.TestCase):
    def test_all_15bit_values_round_trip(self) -> None:
        for value in range(32768):
            bits = [int(bit) for bit in f"{value:015b}"]
            words, _padding = b2t.pack_bits(bits)
            self.assertEqual(len(words), 1)
            self.assertEqual(words[0], value)
            unpacked = b2t.unpack_bits(words, 15)
            self.assertEqual(unpacked, bits)

    def test_pack_bits_rejects_non_bit(self) -> None:
        with self.assertRaises(b2t.B2TError):
            b2t.pack_bits([0, 1, 2])

    def test_unpack_bits_rejects_bit_length_exceeding_payload(self) -> None:
        with self.assertRaises(b2t.B2TError):
            b2t.unpack_bits([0], 16)

    def test_unpack_bits_rejects_extra_cell(self) -> None:
        with self.assertRaises(b2t.B2TError):
            b2t.unpack_bits([0, 0], 15)

    def test_unpack_bits_rejects_non_canonical_word_count(self) -> None:
        with self.assertRaises(b2t.B2TError):
            b2t.unpack_bits([0], 0)

    def test_unpack_bits_rejects_reserved_cell(self) -> None:
        with self.assertRaises(b2t.B2TError):
            b2t.unpack_bits([32768], 15)

    def test_unpack_bits_rejects_nonzero_padding(self) -> None:
        # 8 bits of data require a 15-bit word with 7 zero padding bits.
        with self.assertRaises(b2t.B2TError):
            b2t.unpack_bits([(1 << 6) | 1], 8)


class TestContainerFormat(unittest.TestCase):
    def test_header_layout(self) -> None:
        data = b"hello"
        raw = b2t.encode_bytes(data).container
        magic, version, flags, bit_length, word_count, crc = b2t.HEADER.unpack_from(raw)
        self.assertEqual(magic, b"B2T0")
        self.assertEqual(version, 0)
        self.assertEqual(flags, 0)
        self.assertEqual(bit_length, 40)
        self.assertEqual(word_count, 3)
        self.assertEqual(crc, zlib_crc32(data))

    def test_container_size_matches_word_count(self) -> None:
        encoded = b2t.encode_bytes(b"1234567890")
        self.assertEqual(len(encoded.container), b2t.HEADER.size + 2 * len(encoded.words))

    def test_bad_magic_rejected(self) -> None:
        raw = bytearray(b2t.encode_bytes(b"x").container)
        raw[0:4] = b"XXXX"
        with self.assertRaises(b2t.B2TError):
            b2t.decode_container(bytes(raw))

    def test_bad_version_rejected(self) -> None:
        raw = bytearray(b2t.encode_bytes(b"x").container)
        raw[4] = 99
        with self.assertRaises(b2t.B2TError):
            b2t.decode_container(bytes(raw))

    def test_bad_flags_rejected(self) -> None:
        raw = bytearray(b2t.encode_bytes(b"x").container)
        raw[5] = 1
        with self.assertRaises(b2t.B2TError):
            b2t.decode_container(bytes(raw))

    def test_bad_bit_length_alignment_rejected(self) -> None:
        raw = bytearray(b2t.encode_bytes(b"x").container)
        bit_length = 9  # A non-multiple-of-8 bit length must be rejected.
        struct.pack_into("<Q", raw, 6, bit_length)
        with self.assertRaises(b2t.B2TError):
            b2t.decode_container(bytes(raw))

    def test_bad_word_count_rejected(self) -> None:
        raw = bytearray(b2t.encode_bytes(b"x").container)
        struct.pack_into("<I", raw, 14, 2)
        with self.assertRaises(b2t.B2TError):
            b2t.decode_container(bytes(raw))

    def test_truncated_payload_rejected(self) -> None:
        raw = bytearray(b2t.encode_bytes(b"x").container)
        trimmed = bytes(raw[: len(raw) - 1])
        with self.assertRaises(b2t.B2TError):
            b2t.decode_container(trimmed)

    def test_extra_payload_rejected(self) -> None:
        raw = bytearray(b2t.encode_bytes(b"x").container)
        extended = bytes(raw) + b"\x00\x00"
        with self.assertRaises(b2t.B2TError):
            b2t.decode_container(extended)

    def test_crc_mismatch_rejected(self) -> None:
        raw = bytearray(b2t.encode_bytes(b"hello").container)
        raw[-1] ^= 1
        with self.assertRaises(b2t.B2TError):
            b2t.decode_container(bytes(raw))


class TestTrits(unittest.TestCase):
    def test_word_to_trits_roundtrip(self) -> None:
        for word in (0, 1, 2, 10, 32767, 32768, 59048):
            trits = b2t.word_to_trits(word)
            self.assertEqual(len(trits), 10)
            self.assertEqual(b2t.trits_to_word(trits), word)

    def test_word_to_trits_rejects_out_of_range(self) -> None:
        with self.assertRaises(b2t.B2TError):
            b2t.word_to_trits(-1)
        with self.assertRaises(b2t.B2TError):
            b2t.word_to_trits(59049)

    def test_trits_to_word_rejects_bad_input(self) -> None:
        with self.assertRaises(b2t.B2TError):
            b2t.trits_to_word([0] * 9)
        with self.assertRaises(b2t.B2TError):
            b2t.trits_to_word([3] + [0] * 9)


class TestCLI(unittest.TestCase):
    def test_encode_decode_inspect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp = Path(tmp_dir_name)
            source = tmp / "sample.bin"
            container_path = tmp / "sample.b2t"
            restored = tmp / "sample.restored"
            source.write_bytes(b"B2T codec demo: 15 bits per cell.")

            self.assertEqual(b2t.main(["encode", str(source), "-o", str(container_path)]), 0)
            self.assertTrue(container_path.is_file())

            self.assertEqual(b2t.main(["decode", str(container_path), "-o", str(restored)]), 0)
            self.assertEqual(source.read_bytes(), restored.read_bytes())

            # Inspect must fail on a corrupted container.
            raw = bytearray(container_path.read_bytes())
            raw[-1] ^= 0xFF
            broken_path = tmp / "sample-broken.b2t"
            broken_path.write_bytes(bytes(raw))
            self.assertEqual(b2t.main(["inspect", str(broken_path)]), 1)


def zlib_crc32(data: bytes) -> int:
    import zlib

    return zlib.crc32(data) & 0xFFFFFFFF


if __name__ == "__main__":
    unittest.main()
