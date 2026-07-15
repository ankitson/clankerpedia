#!/usr/bin/env python3
"""Synthesize text with the local OpenAI-compatible Chatterbox TTS API."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://chatterbox-tts:8000/v1"
DEFAULT_MODEL = "chatterbox"
DEFAULT_VOICE = "Alice"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate speech through the local Chatterbox TTS service."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("text", nargs="?", help="Text to synthesize.")
    source.add_argument("--input-file", type=Path, help="UTF-8 text file to synthesize.")
    parser.add_argument("--out", type=Path, required=True, help="Destination audio file.")
    parser.add_argument(
        "--format",
        default="wav",
        help="Audio response format (default: wav).",
    )
    parser.add_argument(
        "--speed", type=float, default=1.0, help="Speech speed (default: 1.0)."
    )
    parser.add_argument("--model", help="Model override (default: chatterbox).")
    parser.add_argument("--voice", help="Voice override (default: Alice).")
    return parser.parse_args()


def read_text(args: argparse.Namespace) -> str:
    if args.input_file is None:
        return args.text
    try:
        return args.input_file.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(f"Could not read {args.input_file}: {error}") from error


def main() -> None:
    args = parse_args()
    text = read_text(args)
    if not text.strip():
        raise SystemExit("Text to synthesize cannot be empty.")

    base_url = os.environ.get("TTS_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = args.model or os.environ.get("TTS_MODEL", DEFAULT_MODEL)
    voice = args.voice or os.environ.get("TTS_VOICE", DEFAULT_VOICE)
    payload = json.dumps(
        {
            "input": text,
            "model": model,
            "voice": voice,
            "response_format": args.format,
            "speed": args.speed,
        }
    ).encode("utf-8")
    request = Request(
        f"{base_url}/audio/speech",
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "audio/*"},
        method="POST",
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with urlopen(request, timeout=120) as response:
            with tempfile.NamedTemporaryFile(
                mode="wb", delete=False, dir=args.out.parent, prefix=f".{args.out.name}."
            ) as temporary:
                temporary_path = Path(temporary.name)
                while chunk := response.read(1024 * 1024):
                    temporary.write(chunk)
        if temporary_path.stat().st_size == 0:
            raise SystemExit("TTS service returned an empty audio response.")
        temporary_path.replace(args.out)
        temporary_path = None
    except HTTPError as error:
        message = error.read(4096).decode("utf-8", errors="replace")
        raise SystemExit(f"TTS API returned HTTP {error.code}: {message}") from error
    except URLError as error:
        raise SystemExit(f"Could not reach TTS API at {base_url}: {error.reason}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print(args.out)


if __name__ == "__main__":
    main()
