#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path
import urllib.error
import urllib.request


FACT_API_URL = "https://uselessfacts.jsph.pl/random.json?language=en"


def fetch_interesting_fact() -> str:
    request = urllib.request.Request(FACT_API_URL)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        raise RuntimeError("Failed to fetch a fun fact. Try again or pass --message.") from exc

    fact = payload.get("text")
    if not fact:
        raise RuntimeError("Fact API response missing 'text' field.")
    return fact


def build_multipart_payload(message: str, attachment: Path) -> tuple[bytes, str]:
    boundary = "----discordwebhookboundary"
    content_type, _ = mimetypes.guess_type(attachment.name)
    content_type = content_type or "application/octet-stream"

    payload_json = json.dumps({"content": message})
    file_bytes = attachment.read_bytes()

    parts = [
        f"--{boundary}\r\n"
        "Content-Disposition: form-data; name=\"payload_json\"\r\n"
        "Content-Type: application/json\r\n\r\n"
        f"{payload_json}\r\n",
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{attachment.name}\"\r\n"
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
        + file_bytes
        + b"\r\n",
        f"--{boundary}--\r\n",
    ]

    body = b"".join(part if isinstance(part, bytes) else part.encode("utf-8") for part in parts)
    return body, boundary


def post_to_discord(webhook_url: str, message: str, attachment: Path | None) -> None:
    if attachment:
        body, boundary = build_multipart_payload(message, attachment)
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        data = body
    else:
        data = json.dumps({"content": message}).encode("utf-8")
        headers = {"Content-Type": "application/json"}

    request = urllib.request.Request(
        webhook_url,
        data=data,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status not in (200, 204):
            raise RuntimeError(f"Discord webhook returned {response.status}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Post an interesting message to Discord via webhook.",
    )
    parser.add_argument(
        "--message",
        help="Custom message to post. If omitted, a fun fact is fetched.",
    )
    parser.add_argument(
        "--webhook",
        help="Discord webhook URL. Defaults to DISCORD_WEBHOOK_URL env var.",
    )
    parser.add_argument(
        "--attachment",
        help="Optional file path to attach.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    webhook_url = args.webhook or os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        webhook_url = input("Enter webhook URL: ").strip()
        if not webhook_url:
            print("Error: Webhook URL is required.", file=sys.stderr)
            return 1

    message = args.message
    if message is None:
        prompt_message = input("Enter message (leave blank to fetch a fun fact): ").strip()
        message = prompt_message or fetch_interesting_fact()

    attachment_path = args.attachment
    if attachment_path is None:
        attachment_path = input("Attachment file path (optional, press Enter to skip): ").strip() or None

    attachment = None
    if attachment_path:
        candidate = Path(attachment_path)
        if not candidate.is_file():
            print(f"Error: Attachment not found: {candidate}", file=sys.stderr)
            return 1
        attachment = candidate

    post_to_discord(webhook_url, message, attachment)
    print("Posted to Discord." if not attachment else "Posted to Discord with attachment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
