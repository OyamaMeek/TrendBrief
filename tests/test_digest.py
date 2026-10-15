import unittest
from datetime import UTC, datetime
from pathlib import Path

import trending_digest as digest


class ParsingTests(unittest.TestCase):
    def test_real_page_order_and_counts(self):
        html = Path("tests/fixtures/trending.html").read_text()
        projects = digest.parse_trending(html)
        self.assertEqual(len(projects), 10)
        self.assertEqual(projects[0].name, "morluto/rea")
        self.assertEqual(projects[1].name, "anthropics/claude-plugins-official")
        self.assertEqual(projects[0].today_stars, 41034)
        self.assertEqual([p.rank for p in projects], list(range(1, 11)))

    def test_missing_fields_are_unknown(self):
        html = "".join(
            f'<article class="Box-row"><h2><a href="/owner/repo{i}">owner / repo{i}</a>'
            "</h2></article>"
            for i in range(10)
        )
        project = digest.parse_trending(html)[0]
        self.assertIsNone(project.stars)
        self.assertIsNone(project.today_stars)
        self.assertEqual(project.language, "未知")

    def test_short_invalid_duplicate_and_mismatched_lists_fail(self):
        for html in ("<html></html>", '<article class="Box-row"></article>' * 10):
            with self.subTest(html=html[:30]), self.assertRaises(digest.DigestError):
                digest.parse_trending(html)
        row = '<article class="Box-row"><h2><a href="/a/b">a / b</a></h2></article>'
        with self.assertRaises(digest.DigestError):
            digest.parse_trending(row * 10)
        with self.assertRaises(digest.DigestError):
            digest.parse_trending(row.replace('href="/a/b"', 'href="https://evil.test/a/b"') * 10)


class FormattingTests(unittest.TestCase):
    def test_project_format_omits_fetch_time_and_retains_stats(self):
        project = digest.Project(
            1, "owner/repo", "https://github.com/owner/repo", "原始描述", "Python", None, 0
        )
        self.assertEqual(
            digest.format_project(project),
            "1. owner/repo\nhttps://github.com/owner/repo\n语言：Python | Star：未知 | 今日新增：0",
        )

    def test_date_paths_and_schedule(self):
        instant = datetime(2026, 10, 15, 18, tzinfo=UTC)
        day = digest.shanghai_now(instant).date().isoformat()
        self.assertEqual(day, "2026-10-16")
        self.assertEqual(digest.paths(Path("."), day)[0], Path("massage/2026/10/16/Trending.md"))
        for hour, expected in ((6, 14), (8, 16), (9, 17)):
            self.assertEqual(digest.shanghai_now(instant.replace(hour=hour)).hour, expected)
        self.assertTrue(digest.should_skip("schedule", instant.replace(hour=5)))
        self.assertFalse(digest.should_skip("workflow_dispatch", instant.replace(hour=5)))

    def test_unicode_chunks_preserve_entries_and_shorten_only_description(self):
        entries = [
            (f"{i}. owner/repo{i}\nhttps://github.com/owner/repo{i}", "😀" * 4000)
            for i in range(1, 11)
        ]
        chunks = digest.split_messages("2026-10-15", entries)
        self.assertEqual(len(chunks), 10)
        for i, chunk in enumerate(chunks, 1):
            self.assertLessEqual(digest.utf16_length(chunk), 3500)
            self.assertIn(f"{i}/10", chunk)
            self.assertIn(f"https://github.com/owner/repo{i}\n", chunk)

    def test_ai_response_validation(self):
        good = {"choices": [{"finish_reason": "stop", "message": {"content": "中" * 100}}]}
        self.assertEqual(digest.ai_content(good), "中" * 100)
        for data in (
            {},
            {"choices": []},
            {"choices": None},
            {"choices": [{"finish_reason": "length", "message": {"content": "中" * 120}}]},
            {"choices": [{"finish_reason": "stop", "message": {"content": None}}]},
        ):
            with self.subTest(data=data), self.assertRaises(digest.DigestError):
                digest.ai_content(data)
        for size in (99, 151):
            with self.assertRaises(digest.DigestError):
                digest.validate_summary("中" * size)
        self.assertEqual(digest.validate_summary("中" * 150), "中" * 150)

    def test_local_send_is_rejected(self):
        with self.assertRaises(digest.DigestError):
            digest.require_actions({})


if __name__ == "__main__":
    unittest.main()
