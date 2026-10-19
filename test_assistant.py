"""
test_assistant.py - Automated Unit Test Suite for AI Voice Assistant
Tests intent classification, regex command parsing, and system telemetry retrieval without live audio hardware.
"""

import unittest
from unittest.mock import patch
from assistant_engine import VoiceAssistantEngine


class TestVoiceAssistantEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = VoiceAssistantEngine()

    def test_engine_initialization(self):
        """Verify engine properties and initial state."""
        self.assertIsNotNone(self.engine.recognizer)
        self.assertIsNotNone(self.engine.tts)
        self.assertEqual(self.engine.status, "Idle")

    def test_time_intent(self):
        """Verify time query produces valid formatted time response."""
        res = self.engine.execute_command("what time is it")
        self.assertEqual(res["intent"], "time")
        self.assertIn("The current time is", res["response"])
        self.assertFalse(res["should_exit"])

    def test_date_intent(self):
        """Verify date query produces valid formatted date response."""
        res = self.engine.execute_command("tell me today's date")
        self.assertEqual(res["intent"], "date")
        self.assertIn("Today is", res["response"])
        self.assertFalse(res["should_exit"])

    def test_system_telemetry_intent(self):
        """Verify telemetry returns CPU, RAM, and Battery readings."""
        res = self.engine.execute_command("check battery and cpu status")
        self.assertEqual(res["intent"], "system_telemetry")
        self.assertIn("data", res)
        self.assertIn("cpu_percent", res["data"])
        self.assertIn("ram_percent", res["data"])
        self.assertGreaterEqual(res["data"]["cpu_percent"], 0.0)
        self.assertGreaterEqual(res["data"]["ram_percent"], 0.0)

    @patch("webbrowser.open")
    def test_web_open_intent(self, mock_web_open):
        """Verify web target extraction."""
        res = self.engine.execute_command("open youtube")
        self.assertEqual(res["intent"], "web_open")
        self.assertEqual(res["action"], "open_url")
        self.assertIn("youtube.com", res.get("url", ""))
        mock_web_open.assert_called_once_with("https://www.youtube.com")

    @patch("webbrowser.open")
    def test_web_search_intent(self, mock_web_open):
        """Verify search query parameter extraction."""
        res = self.engine.execute_command("search google for artificial intelligence")
        self.assertEqual(res["intent"], "web_search")
        self.assertIn("artificial intelligence", res.get("query", ""))
        self.assertIn("google.com/search", res.get("url", ""))
        mock_web_open.assert_called_once()

    @patch("subprocess.Popen")
    def test_app_launch_intent(self, mock_popen):
        """Verify application launch targeting."""
        res = self.engine.execute_command("open notepad")
        self.assertEqual(res["intent"], "app_launch")
        self.assertEqual(res.get("app"), "notepad.exe")
        mock_popen.assert_called_with(["notepad.exe"])

        res_calc = self.engine.execute_command("open calculator")
        self.assertEqual(res_calc["intent"], "app_launch")
        self.assertEqual(res_calc.get("app"), "calc.exe")
        mock_popen.assert_called_with(["calc.exe"])

    def test_session_termination_intent(self):
        """Verify exit commands trigger should_exit flag."""
        res = self.engine.execute_command("quit")
        self.assertEqual(res["intent"], "exit")
        self.assertTrue(res["should_exit"])

    def test_empty_and_unknown_commands(self):
        """Verify graceful fallback for empty or out-of-domain commands."""
        res_empty = self.engine.execute_command("   ")
        self.assertEqual(res_empty["intent"], "empty")

        res_unknown = self.engine.execute_command("some random unmapped command 999")
        self.assertEqual(res_unknown["intent"], "unknown")
        self.assertIn("I heard", res_unknown["response"])


if __name__ == "__main__":
    unittest.main()
