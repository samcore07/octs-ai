"""
Octs AI - Configuration & Tracing Unit Tests
"""

import os
import unittest
from backend.config import Settings
from backend.tracing import setup_tracing


class TestConfigAndTracing(unittest.TestCase):
    def test_default_settings(self):
        """Verify default configuration values."""
        settings = Settings(gemini_api_key="test-key")
        self.assertEqual(settings.model_name, "gemini-3.5-flash-lite")
        self.assertEqual(settings.model_provider, "google_genai")
        self.assertEqual(settings.langsmith_tracing, False)
        self.assertIn("writers", settings.allowed_disciplines)
        self.assertIn("musicians", settings.allowed_disciplines)
        self.assertIn("creators", settings.allowed_disciplines)
        self.assertIn("designers", settings.allowed_disciplines)

    def test_cors_origins_parsing(self):
        """Verify CORS comma-separated string parsing."""
        settings = Settings(
            gemini_api_key="test-key",
            cors_origins="https://app.octs.ai, https://admin.octs.ai",
        )
        self.assertEqual(
            settings.cors_origins,
            ["https://app.octs.ai", "https://admin.octs.ai"],
        )

    def test_tracing_disabled_by_default(self):
        """Verify setup_tracing returns False when disabled."""
        settings = Settings(gemini_api_key="test-key", langsmith_tracing=False)
        result = setup_tracing(settings)
        self.assertFalse(result)
        self.assertEqual(os.environ.get("LANGSMITH_TRACING"), "false")

    def test_tracing_missing_api_key_graceful(self):
        """Verify setup_tracing fails gracefully when key is missing or empty."""
        settings = Settings(
            gemini_api_key="test-key",
            langsmith_tracing=True,
            langsmith_api_key="",
        )
        result = setup_tracing(settings)
        self.assertFalse(result)
        self.assertEqual(os.environ.get("LANGSMITH_TRACING"), "false")

    def test_tracing_enabled_with_valid_key(self):
        """Verify setup_tracing enables environment correctly with valid key."""
        settings = Settings(
            gemini_api_key="test-key",
            langsmith_tracing=True,
            langsmith_api_key="lsv2_pt_testkey123456789",
            langsmith_project="octs-test",
        )
        result = setup_tracing(settings)
        self.assertTrue(result)
        self.assertEqual(os.environ.get("LANGSMITH_TRACING"), "true")
        self.assertEqual(os.environ.get("LANGSMITH_PROJECT"), "octs-test")
        self.assertEqual(os.environ.get("LANGSMITH_API_KEY"), "lsv2_pt_testkey123456789")


if __name__ == "__main__":
    unittest.main()
