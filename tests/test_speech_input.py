import io
import unittest
import wave
from unittest.mock import Mock

import speech_input


class SpeechInputTests(unittest.TestCase):
    def test_stereo_downmix(self):
        stereo = (1000).to_bytes(2, "little", signed=True) + (3000).to_bytes(2, "little", signed=True)
        mono = speech_input._stereo_to_mono(stereo)
        self.assertEqual(int.from_bytes(mono, "little", signed=True), 2000)

    def test_wav_is_mono_16k(self):
        data = speech_input._wav_bytes(b"\x00\x00" * 160)
        with wave.open(io.BytesIO(data), "rb") as handle:
            self.assertEqual(handle.getnchannels(), 1)
            self.assertEqual(handle.getframerate(), 16000)
            self.assertEqual(handle.getsampwidth(), 2)

    def test_transcription_request(self):
        response = Mock()
        response.status_code = 200
        response.raise_for_status.return_value = None
        response.json.return_value = {"text": "  Love.  "}
        session = Mock()
        session.post.return_value = response
        result = speech_input.transcribe(b"RIFF", api_key="test-key", prompt="Choose Love", session=session)
        self.assertEqual(result, "Love.")
        call = session.post.call_args
        data = dict(call.kwargs["data"])
        self.assertEqual(data["model"], "gpt-transcribe")
        self.assertEqual(data["language"], "en")
        self.assertEqual(data["keywords[]"], "Madame Maxine")
        self.assertNotIn("test-key", repr(call.kwargs["files"]))

    def test_missing_key_is_recoverable(self):
        with self.assertRaisesRegex(speech_input.SpeechInputError, "OPENAI_API_KEY"):
            speech_input.transcribe(b"RIFF", api_key="")

    def test_api_error_reports_safe_code(self):
        response = Mock()
        response.status_code = 429
        response.json.return_value = {
            "error": {"code": "credit_balance_exhausted", "message": "No credits"}
        }
        session = Mock()
        session.post.return_value = response
        with self.assertRaisesRegex(speech_input.SpeechInputError, "credit_balance_exhausted"):
            speech_input.transcribe(b"RIFF", api_key="test-key", session=session)


if __name__ == "__main__":
    unittest.main()
