import copy
import json
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

import httpx
from test_network import local_server

import trending_digest as digest


def sample_state():
    entries = [
        (f"{i}. owner/repo{i}\nhttps://github.com/owner/repo{i}", "中" * 3000) for i in range(1, 11)
    ]
    generated = digest.Digest(
        "2026-10-15", "2026-10-15T15:00:00+08:00", [], digest.split_messages("2026-10-15", entries)
    )
    return digest.new_delivery(generated, digest.fingerprint("-123"))


class StateTests(unittest.TestCase):
    def test_startup_date_stays_fixed_across_midnight(self):
        state = sample_state()
        state["fetched_at"] = "2026-10-16T00:01:00+08:00"
        archive = digest.render_archive(state)
        state["archive_sha256"] = digest.checksum(archive)
        digest.validate_delivery(state, "2026-10-15", state["target"], archive)

    def test_state_round_trip_and_corruption(self):
        state = sample_state()
        archive = digest.render_archive(state)
        digest.validate_delivery(state, state["date"], state["target"], archive)
        for modify in (
            lambda x: x.update(target="wrong"),
            lambda x: x.update(archive_sha256="0" * 64),
            lambda x: x.update(date="2026-10-16"),
            lambda x: x["messages"][0].update(status="sent", message_id=None),
            lambda x: x["messages"][0].update(status="pending", message_id=12),
            lambda x: x["messages"][0].update(status="broken"),
            lambda x: x["messages"][0].update(text="tampered"),
            lambda x: x.update(messages=[]),
        ):
            corrupted = copy.deepcopy(state)
            modify(corrupted)
            with self.subTest(modify=modify), self.assertRaises(digest.DigestError):
                digest.validate_delivery(corrupted, state["date"], state["target"], archive)

    def test_manual_resolution_retains_body_and_other_parts(self):
        state = sample_state()
        archive = digest.render_archive(state)
        state["messages"][0].update(status="uncertain")
        state["messages"][0].update(status="sent", message_id=123)
        digest.validate_delivery(state, state["date"], state["target"], archive)
        self.assertEqual(digest.render_archive(state), archive)
        state["messages"][1].update(status="pending", message_id=None)
        digest.validate_delivery(state, state["date"], state["target"], archive)


class GitDeliveryTests(unittest.TestCase):
    def setUp(self):
        Path(".local-test").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=".local-test")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.remote = self.base / "remote.git"
        self.root = self.base / "work"
        self.git(self.base, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git(self.base, "init", "-b", "main", str(self.root))
        self.git(self.root, "config", "user.name", "Test")
        self.git(self.root, "config", "user.email", "test@example.invalid")
        (self.root / "seed").write_text("initial\n")
        self.git(self.root, "add", "seed")
        self.git(self.root, "commit", "-m", "test: initialize")
        self.git(self.root, "remote", "add", "origin", str(self.remote))
        self.git(self.root, "push", "-u", "origin", "main")
        self.store = digest.GitStore(self.root, "main", digest.Budget())
        self.store.preflight()
        self.state = sample_state()

    def git(self, root, *args):
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, check=True
        ).stdout.decode()

    def send_local(self, state, replies):
        with local_server(replies) as (url, calls), httpx.Client() as client:
            sender = digest.Telegram(digest.Network(client, digest.Budget()), "token", "-123")
            sender.url = url
            digest.deliver(self.store, state, sender)
            return calls

    def test_initial_commit_and_partial_resume_without_regeneration(self):
        self.store.save(self.state, create=True)
        first = self.state["messages"][0]
        first.update(status="sent", message_id=99)
        self.store.save(self.state)
        frozen = digest.render_archive(self.state)
        loaded = digest.load_delivery(self.store, self.state["date"], self.state["target"])
        count = len(loaded["messages"]) - 1
        replies = [
            (200, json.dumps({"ok": True, "result": {"message_id": i + 100}}).encode(), {})
            for i in range(count)
        ]
        self.assertEqual(len(self.send_local(loaded, replies)), count)
        loaded = digest.load_delivery(self.store, self.state["date"], self.state["target"])
        self.assertTrue(all(m["status"] == "sent" for m in loaded["messages"]))
        self.assertEqual(self.send_local(loaded, []), [])
        self.assertEqual(digest.render_archive(loaded), frozen)
        remote = self.git(self.root, "show", "origin/main:.state/2026/10/15/delivery.json")
        self.assertTrue(all(m["status"] == "sent" for m in json.loads(remote)["messages"]))

    def test_sending_becomes_uncertain_and_blocks_all_sends(self):
        self.store.save(self.state, create=True)
        self.state["messages"][0].update(status="sending")
        self.store.save(self.state)
        with self.assertRaises(digest.DigestError):
            digest.load_delivery(self.store, self.state["date"], self.state["target"])
        remote = self.git(self.root, "show", "origin/main:.state/2026/10/15/delivery.json")
        self.assertEqual(json.loads(remote)["messages"][0]["status"], "uncertain")

    def test_complete_day_skips_without_ai_or_bot_credentials(self):
        for i, message in enumerate(self.state["messages"], 1):
            message.update(status="sent", message_id=i)
        self.store.save(self.state, create=True)
        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": "owner/repo",
            "TRENDBRIEF_DEFAULT_BRANCH": "main",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_SERVER_URL": "https://github.com",
            "GITHUB_WORKFLOW_REF": "owner/repo/.github/workflows/trendbrief.yml@refs/heads/main",
            "TELEGRAM_CHAT_ID": "-123",
        }
        digest.run(False, env, self.root, datetime(2026, 10, 15, 7, tzinfo=UTC))

    def test_explicit_rejection_returns_pending_and_timeout_is_uncertain(self):
        for code, payload, expected in (
            (403, {"ok": False, "error_code": 403}, "pending"),
            (500, {}, "uncertain"),
        ):
            self.state["messages"][0].update(status="pending", message_id=None)
            self.store.save(
                self.state, create=not digest.paths(self.root, self.state["date"])[0].exists()
            )
            with self.assertRaises(digest.DeliveryError):
                self.send_local(self.state, [(code, json.dumps(payload).encode(), {})])
            remote = self.git(self.root, "show", "origin/main:.state/2026/10/15/delivery.json")
            self.assertEqual(json.loads(remote)["messages"][0]["status"], expected)
            self.assertEqual(json.loads(remote)["messages"][1]["status"], "pending")

    def test_push_failure_prevents_send(self):
        self.store.save(self.state, create=True)
        self.git(self.root, "remote", "set-url", "--push", "origin", str(self.base / "absent.git"))
        with local_server([]) as (url, calls), httpx.Client() as client:
            sender = digest.Telegram(digest.Network(client, digest.Budget()), "token", "-123")
            sender.url = url
            with self.assertRaises(digest.DigestError):
                digest.deliver(self.store, self.state, sender)
        self.assertEqual(calls, [])
        remote = self.git(self.root, "show", "origin/main:.state/2026/10/15/delivery.json")
        self.assertEqual(json.loads(remote)["messages"][0]["status"], "pending")

    def test_sent_save_failure_leaves_remote_sending_and_stops(self):
        self.store.save(self.state, create=True)

        def reject_next_push():
            self.git(
                self.root, "remote", "set-url", "--push", "origin", str(self.base / "absent.git")
            )

        reply = (200, b'{"ok":true,"result":{"message_id":42}}', {})
        with local_server([reply], on_request=reject_next_push) as (url, calls):
            with httpx.Client() as client:
                sender = digest.Telegram(digest.Network(client, digest.Budget()), "token", "-123")
                sender.url = url
                with self.assertRaises(digest.DigestError):
                    digest.deliver(self.store, self.state, sender)
        self.assertEqual(len(calls), 1)
        remote = self.git(self.root, "show", "origin/main:.state/2026/10/15/delivery.json")
        self.assertEqual(json.loads(remote)["messages"][0]["status"], "sending")
        self.assertEqual(json.loads(remote)["messages"][1]["status"], "pending")

    def test_pending_save_failure_leaves_remote_sending_and_stops(self):
        self.store.save(self.state, create=True)

        def reject_next_push():
            self.git(
                self.root, "remote", "set-url", "--push", "origin", str(self.base / "absent.git")
            )

        reply = (403, b'{"ok":false,"error_code":403}', {})
        with local_server([reply], on_request=reject_next_push) as (url, calls):
            with httpx.Client() as client:
                sender = digest.Telegram(digest.Network(client, digest.Budget()), "token", "-123")
                sender.url = url
                with self.assertRaises(digest.DigestError):
                    digest.deliver(self.store, self.state, sender)
        self.assertEqual(len(calls), 1)
        remote = self.git(self.root, "show", "origin/main:.state/2026/10/15/delivery.json")
        self.assertEqual(json.loads(remote)["messages"][0]["status"], "sending")

    def test_commit_failure_prevents_send(self):
        self.store.save(self.state, create=True)
        self.git(self.root, "config", "commit.gpgsign", "true")
        self.git(self.root, "config", "gpg.program", str(self.base / "absent-gpg"))
        with local_server([]) as (url, calls), httpx.Client() as client:
            sender = digest.Telegram(digest.Network(client, digest.Budget()), "token", "-123")
            sender.url = url
            with self.assertRaises(digest.DigestError):
                digest.deliver(self.store, self.state, sender)
        self.assertEqual(calls, [])

    def test_orphan_and_damaged_files_are_not_overwritten(self):
        archive, state_path = digest.paths(self.root, self.state["date"])
        digest.atomic_write(archive, b"orphan")
        with self.assertRaises(digest.DigestError):
            digest.load_delivery(self.store, self.state["date"], self.state["target"])
        self.assertEqual(archive.read_bytes(), b"orphan")
        digest.atomic_write(state_path, b"not json")
        with self.assertRaises(digest.DigestError):
            digest.load_delivery(self.store, self.state["date"], self.state["target"])
        self.assertEqual(state_path.read_bytes(), b"not json")


if __name__ == "__main__":
    unittest.main()
