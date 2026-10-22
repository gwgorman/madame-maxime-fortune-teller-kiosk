import unittest

from lightelf_bounded_test import MAX_DURATION, tiny_diamond_packet
from lightelf_probe import expected_challenge, parse_query_reply, query_packet


class LightElfProbeTests(unittest.TestCase):
    def test_query_packet_is_bounded_identity_envelope(self):
        challenge = bytes((0x12, 0x34, 0x56, 0x78))
        self.assertEqual(
            query_packet(challenge), bytes.fromhex("E0E1E2E312345678E4E5E6E7")
        )

    def test_bounded_optical_packet_is_fixed_tiny_diamond(self):
        packet = tiny_diamond_packet()
        self.assertEqual(packet[:4], bytes.fromhex("F0F1F2F3"))
        self.assertEqual(packet[-4:], bytes.fromhex("F4F5F6F7"))
        self.assertEqual(int.from_bytes(packet[20:22], "big"), 17)
        self.assertEqual(len(packet), 111)
        self.assertEqual(MAX_DURATION, 2.0)

    def test_challenge_formula_matches_reference(self):
        self.assertEqual(
            expected_challenge(bytes((0x12, 0x34, 0x56, 0x78))),
            bytes((0x1A, 0xE7, 0x6A, 0x53)),
        )

    def test_parse_valid_reply(self):
        challenge = bytes((0x12, 0x34, 0x56, 0x78))
        reply = (
            bytes.fromhex("E0E1E2E3")
            + bytes((7, 0x01, 0x23))
            + expected_challenge(challenge)
            + bytes((0, 2, 4, 9))
            + bytes.fromhex("E4E5E6E7")
        )
        parsed = parse_query_reply(reply, challenge)
        self.assertEqual(parsed.query_attempts, 1)
        self.assertTrue(parsed.challenge_ok)
        self.assertFalse(parsed.device_on)
        self.assertEqual(parsed.device_type, 2)
        self.assertEqual(parsed.protocol_version, 4)
        self.assertEqual(parsed.device_number, 7)
        self.assertEqual(parsed.user_number, 9)
        self.assertEqual(parsed.ota_version_raw, 0x0123)

        retried = parse_query_reply(reply, challenge, query_attempts=2)
        self.assertEqual(retried.query_attempts, 2)

    def test_parse_rejects_short_reply(self):
        with self.assertRaises(ValueError):
            parse_query_reply(b"short", b"1234")


if __name__ == "__main__":
    unittest.main()
