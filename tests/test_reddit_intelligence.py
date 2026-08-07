import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.reddit_monitor.intelligence.dashboard import DashboardStore
from scripts.reddit_monitor.intelligence.pipeline import match_groups, run_pipeline, validate_score
from scripts.reddit_monitor.intelligence.profiles import load_profile
from scripts.reddit_monitor.intelligence.pipeline import sheet_row
from scripts.reddit_monitor.intelligence.sources import collect_reddit_rss


PROFILE = Path(__file__).parents[1] / "scripts" / "reddit_monitor" / "intelligence" / "profiles" / "example.json"


class RedditIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(PROFILE)

    def test_group_qualifier_is_local_and_required(self):
        self.assertEqual(match_groups({"title": "consultant needed", "body": ""}, self.profile), [])
        matches = match_groups({"title": "recommend a consultant", "body": ""}, self.profile)
        self.assertEqual(matches[0]["group"], "Broad category")
        self.assertEqual(matches[0]["qualifiers"], ["recommend"])

    def test_score_contract_rejects_out_of_range(self):
        with self.assertRaisesRegex(ValueError, "commercial_intent"):
            validate_score({"commercial_intent": 11, "content_value": 5, "reputation_risk": 1})

    def test_pipeline_persists_contracts_and_deduplicates(self):
        item = {"id": "p1", "title": "Is Example Company worth the price?", "body": "",
                "url": "https://reddit.example/p1", "subreddit": "local"}
        with tempfile.TemporaryDirectory() as tmp:
            first = run_pipeline([item], self.profile, tmp)
            second = run_pipeline([item], self.profile, tmp)
            self.assertEqual(first["opportunities"], 1)
            self.assertEqual(second["opportunities"], 1)
            self.assertEqual(json.loads((Path(tmp) / "run-manifest.json").read_text())["external_effects"], [])
            self.assertTrue((Path(tmp) / "weekly-digest.preview.json").exists())
            self.assertEqual(len((Path(tmp) / "opportunities.jsonl").read_text().splitlines()), 1)

    def test_live_flags_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "approved provider adapter"):
                run_pipeline([], self.profile, tmp, activate_email=True)

    def test_evidence_quote_must_be_source_backed(self):
        def scorer(item, matches, profile):
            return {"commercial_intent": 8, "content_value": 8, "reputation_risk": 1,
                    "evidence_quote": "invented quote"}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "verbatim"):
                run_pipeline([{"id": "x", "title": "Example Company", "body": ""}], self.profile, tmp, scorer)

    def test_evidence_quote_is_required(self):
        def scorer(item, matches, profile):
            return {"commercial_intent": 8, "content_value": 8, "reputation_risk": 1,
                    "evidence_quote": ""}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "required"):
                run_pipeline([{"id": "x", "title": "Example Company", "body": ""}], self.profile, tmp, scorer)

    def test_dashboard_source_url_rejects_non_http_scheme(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "http or https"):
                run_pipeline([{"id": "x", "title": "Example Company", "body": "", "url": "javascript:alert(1)"}], self.profile, tmp)

    def test_dashboard_state_and_status_transition(self):
        item = {"id": "p2", "title": "Example Company review", "body": "",
                "url": "https://reddit.example/p2", "subreddit": "local"}
        with tempfile.TemporaryDirectory() as tmp:
            run_pipeline([item], self.profile, tmp)
            store = DashboardStore(PROFILE, tmp)
            self.assertEqual(store.state()["activation"]["external_effects"], [])
            updated = store.update_status("p2", "Approved")
            self.assertEqual(updated["status"], "Approved")
            with self.assertRaisesRegex(ValueError, "not allowed"):
                store.update_status("p2", "Auto-posted")

    def test_sheet_row_contract_is_stable(self):
        row = {"captured_at": "2026-01-01T00:00:00Z", "published_at": "", "subreddit": "local",
               "title": "Question?", "treatment_or_topic": "service", "geography": "Local",
               "commercial_intent": 8, "content_value": 9, "reputation_risk": 1,
               "suggested_action": "Create content", "url": "https://reddit.example/x",
               "status": "New", "evidence_quote": "Question?"}
        mapped = sheet_row(row)
        self.assertEqual(mapped["Question"], "Question?")
        self.assertEqual(mapped["Team owner"], "")

    def test_public_rss_collection_uses_profile_and_is_read_only(self):
        feed = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>t3_x</id><title>Example Company?</title><link href="https://reddit.example/x"/><content>Question body</content><published>2026-01-01T00:00:00Z</published></entry></feed>'''
        profile = dict(self.profile)
        profile["sources"] = {"reddit_rss": {"enabled": True, "subreddits": ["smallbusiness"], "posts_per_sub": 5}}

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return feed

        with patch("scripts.reddit_monitor.intelligence.sources.urlopen", return_value=Response()) as request:
            rows = collect_reddit_rss(profile)
        self.assertEqual(rows[0]["id"], "t3_x")
        self.assertEqual(rows[0]["subreddit"], "smallbusiness")
        self.assertIn("/new.rss", request.call_args.args[0].full_url)


if __name__ == "__main__":
    unittest.main()
