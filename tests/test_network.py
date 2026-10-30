import json
import threading
import time
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

import trending_digest as digest


@contextmanager
def local_server(replies, on_request=None, byte_delay=0):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            requests.append((self.path, dict(self.headers), body))
            if on_request:
                on_request()
            status, data, headers = replies.pop(0) if replies else (500, b"{}", {})
            if status is None:
                self.close_connection = True
                return
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                if byte_delay:
                    for byte in data:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(byte_delay)
                else:
                    self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        do_POST = do_GET

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class NetworkTests(unittest.TestCase):
    def test_hard_deadline_interrupts_drip_body_and_waiting_headers(self):
        for delay_headers in (False, True):
            with self.subTest(delay_headers=delay_headers):
                on_request = (lambda: time.sleep(0.5)) if delay_headers else None
                with (
                    local_server(
                        [(200, b"abcdefghijk", {})], on_request=on_request, byte_delay=0.04
                    ) as (url, _),
                    httpx.Client() as client,
                ):
                    started = time.monotonic()
                    with self.assertRaises(digest.DigestError) as caught:
                        with digest.execution_timeout(0.1):
                            digest.Network(client, digest.Budget()).request("GET", url, limit=100)
                    self.assertEqual(caught.exception.data["type"], "deadline")
                    self.assertLess(time.monotonic() - started, 0.3)

    def test_bounded_http_retries_and_truncation(self):
        with local_server([(429, b"", {"Retry-After": "0"}), (200, b"abcdef", {})]) as (url, calls):
            with httpx.Client() as client:
                network = digest.Network(client, digest.Budget())
                status, raw, truncated = network.request("GET", url, limit=3, truncate=True)
        self.assertEqual((status, raw, truncated), (200, b"abc", True))
        self.assertEqual(len(calls), 2)

    def test_response_size_and_deadline_fail(self):
        with local_server([(200, b"abcdef", {})]) as (url, _), httpx.Client() as client:
            with self.assertRaises(digest.DigestError):
                digest.Network(client, digest.Budget()).request("GET", url, limit=3)
        with self.assertRaises(digest.DigestError):
            digest.Budget(seconds=0).check()

    def test_ai_length_correction_and_explicit_budget(self):
        def reply(content):
            return (
                200,
                json.dumps(
                    {"choices": [{"finish_reason": "stop", "message": {"content": content}}]}
                ).encode(),
                {},
            )

        with local_server([reply("短"), reply("中文" * 60)]) as (url, calls):
            config = digest.AIConfig(url, "test-secret", "test-model", "max_tokens")
            project = digest.Project(1, "a/b", "https://github.com/a/b", "说明", "未知", None, None)
            with httpx.Client() as client:
                summary = digest.summarize(
                    digest.Network(client, digest.Budget()), config, project, "不可信 README", ""
                )
        self.assertEqual(len(summary), 120)
        self.assertEqual(len(calls), 2)
        for path, _, body in calls:
            payload = json.loads(body)
            self.assertEqual(path, "/chat/completions")
            self.assertEqual(payload["max_tokens"], 1024)
            self.assertNotIn("test-secret", json.dumps(payload))
            self.assertIn("不可信", payload["messages"][0]["content"])

    def test_ai_config_rejects_unverified_budget_and_unsafe_url(self):
        for env in (
            {},
            {"AI_BASE_URL": "https://provider.test/v1", "AI_MODEL": "x", "AI_API_KEY": "secret"},
            {
                "AI_BASE_URL": "http://provider.test/v1",
                "AI_MODEL": "x",
                "AI_API_KEY": "secret",
                "AI_TOKEN_BUDGET_FIELD": "max_tokens",
            },
        ):
            with self.assertRaises(digest.DigestError):
                digest.AIConfig.from_env(env)

    def test_telegram_requires_valid_confirmation(self):
        for status, payload, expected in (
            (200, {"ok": True, "result": {"message_id": 12}}, 12),
            (200, {"ok": True, "result": {"message_id": True}}, "uncertain"),
            (200, {"ok": False}, "uncertain"),
            (500, {}, "uncertain"),
            (403, {"ok": False, "error_code": 403}, "pending"),
            (429, {"ok": False, "error_code": 429, "parameters": {"retry_after": 0}}, "pending"),
        ):
            with self.subTest(status=status, payload=payload):
                response = httpx.Response(status, json=payload)
                if isinstance(expected, int):
                    self.assertEqual(digest.telegram_result(status, response.content), expected)
                else:
                    with self.assertRaises(digest.DeliveryError) as caught:
                        digest.telegram_result(status, response.content)
                    self.assertEqual(caught.exception.delivery_status, expected)

    def test_send_message_plain_text_and_no_preview(self):
        response = (200, b'{"ok":true,"result":{"message_id":42}}', {})
        with local_server([response]) as (url, calls), httpx.Client() as client:
            sender = digest.Telegram(digest.Network(client, digest.Budget()), "token", "-123")
            sender.url = url
            self.assertEqual(sender.send("正文"), 42)
        payload = json.loads(calls[0][2])
        self.assertEqual(payload["chat_id"], "-123")
        self.assertNotIn("message_thread_id", payload)
        self.assertNotIn("parse_mode", payload)
        self.assertTrue(payload["link_preview_options"]["is_disabled"])

    def test_send_message_to_forum_topic(self):
        response = (200, b'{"ok":true,"result":{"message_id":42}}', {})
        with local_server([response]) as (url, calls), httpx.Client() as client:
            sender = digest.Telegram(digest.Network(client, digest.Budget()), "token", "-123", 43)
            sender.url = url
            self.assertEqual(sender.send("正文"), 42)
        self.assertEqual(json.loads(calls[0][2])["message_thread_id"], 43)

    def test_telegram_does_not_retry_connection_interruption(self):
        with local_server([(None, b"", {})]) as (url, calls), httpx.Client() as client:
            sender = digest.Telegram(digest.Network(client, digest.Budget()), "token", "-123")
            sender.url = url
            with self.assertRaises(digest.DeliveryError) as caught:
                sender.send("正文")
        self.assertEqual(caught.exception.delivery_status, "uncertain")
        self.assertEqual(len(calls), 1)

    def test_telegram_429_retries_at_most_three_times(self):
        raw = b'{"ok":false,"error_code":429,"parameters":{"retry_after":0}}'
        with local_server([(429, raw, {})] * 3) as (url, calls), httpx.Client() as client:
            sender = digest.Telegram(digest.Network(client, digest.Budget()), "token", "-123")
            sender.url = url
            with self.assertRaises(digest.DeliveryError) as caught:
                sender.send("正文")
        self.assertEqual(caught.exception.delivery_status, "pending")
        self.assertEqual(len(calls), 3)

    def test_invalid_content_encoding_is_sanitized(self):
        with local_server([(200, b"invalid gzip", {"Content-Encoding": "gzip"})]) as (url, _):
            with httpx.Client() as client, self.assertRaises(digest.DigestError):
                digest.Network(client, digest.Budget(seconds=1)).request("GET", url, limit=100)


if __name__ == "__main__":
    unittest.main()
