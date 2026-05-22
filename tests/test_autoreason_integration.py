import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Adjust path to find scripts
from scripts.ads.ad_loop import (
    IS_LOCAL,
    AD_FLAG,
    step_flag,
    step_generate_variants,
)
from scripts.ads.autoreason.trace import AdCopy

class TestAutoReasonIntegration(unittest.TestCase):

    def test_local_path_fallbacks(self):
        """Verify that IS_LOCAL flag is set correctly and paths are adjusted on Windows/local."""
        self.assertTrue(IS_LOCAL, "Since /opt/cmo-analytics does not exist, IS_LOCAL should be True.")
        self.assertFalse(AD_FLAG.startswith("/opt/"), "AD_FLAG should point to local repo path.")

    @patch("scripts.ads.ad_loop.Path.exists")
    def test_step_flag_fallback(self, mock_exists):
        """Verify that step_flag returns dummy campaigns locally when ad_flag.py is missing."""
        mock_exists.return_value = False
        flagged = step_flag(days=7, dry_run=True)
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["campaign_id"], "120211234567890")
        self.assertEqual(flagged[0]["name"], "kaicalls_broad_smb")
        self.assertIn("CTR below threshold", flagged[0]["flag_reasons"][0])

    @patch("scripts.ads.autoreason.loop.run_loop")
    def test_step_generate_variants_autoreason(self, mock_run_loop):
        """Verify that step_generate_variants executes the AutoReason loop and returns the winner's copy."""
        # Setup mock winner
        mock_winner = AdCopy(
            headline="Mocked AI Headline",
            primary_text="Mocked primary body text with positioning lock.",
            description="Mocked short description",
            cta="LEARN_MORE",
            link="https://kaicalls.com"
        )
        mock_run_loop.return_value = (mock_winner, [], "converged: incumbent won 2 consecutive passes")

        flagged = [{
            "campaign_id": "120211234567890",
            "name": "kaicalls_broad_smb",
            "flag_reasons": ["High CPL"],
        }]

        # Call with autoreason=True
        variants = step_generate_variants(flagged, site="kaicalls", dry_run=True, autoreason=True)

        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0]["headline"], "Mocked AI Headline")
        self.assertEqual(variants[0]["description"], "Mocked primary body text with positioning lock.")
        self.assertEqual(variants[0]["campaign_id"], "120211234567890")
        mock_run_loop.assert_called_once()

    @patch("scripts.ads.autoreason.loop.run_loop")
    def test_step_generate_variants_autoreason_fallback(self, mock_run_loop):
        """Verify that step_generate_variants falls back to standard/dummy generation if AutoReason fails."""
        mock_run_loop.side_effect = Exception("OpenRouter API Error")

        flagged = [{
            "campaign_id": "120211234567890",
            "name": "kaicalls_broad_smb",
            "flag_reasons": ["High CPL"],
        }]

        # Call with autoreason=True, but should fall back to dry run mock copy
        variants = step_generate_variants(flagged, site="kaicalls", dry_run=True, autoreason=True)

        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0]["headline"], "[DRY RUN] AI Call Answering for Law Firms")
        self.assertEqual(variants[0]["description"], "[DRY RUN] 24/7 AI receptionist. Never miss a lead. Try free.")
