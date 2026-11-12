import unittest
import bf16


class EchoTests(unittest.TestCase):
    def test_every_byte_and_eof(self):
        for value in range(256):
            output, status, _, consumed = bf16.run(',+[-.,+]', bytes([value]))
            self.assertEqual((output, status, consumed), (bytes([value]), 'HALTED', 1))
        self.assertEqual(bf16.run(',+[-.,+]', b'')[:2], (b'', 'HALTED'))

    def test_bad_eof_and_missing_output_are_detectable(self):
        output, status, _, _ = bf16.run(',+[-.,+]', b'', eof=0, limit=100)
        self.assertEqual(status, 'MAX_STEPS')
        self.assertNotEqual(output, b'')
        self.assertEqual(bf16.run(',+[-,+]', b'A')[:2], (b'', 'HALTED'))

    def test_malformed_programs_and_underflow_fail(self):
        for source in ('[', ']', '<'):
            with self.assertRaises(ValueError):
                bf16.run(source, b'')


if __name__ == '__main__':
    unittest.main()
