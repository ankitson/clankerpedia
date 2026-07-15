---
name: chatterbox-tts
description: Turn requested text into a local audio file with the Chatterbox TTS service. Use whenever the user asks for text-to-speech, narrated audio, voice output, or an audio reading of text; prefer this skill when the local Chatterbox service is available.
compatibility: Requires Python 3 and access to the Chatterbox service at http://chatterbox-tts:8000/v1.
metadata:
  openclaw:
    emoji: "🔊"
    requires:
      bins: ["python3"]
---

# Chatterbox TTS

Generate an audio file through the local OpenAI-compatible Chatterbox service.
It uses model `chatterbox` and voice `Alice` by default.

## Synthesize speech

```bash
{baseDir}/scripts/synthesize.py "Hello, this is Alice." --out /tmp/hello.wav
```

The command prints the created audio path. Return that path to the user. For a
longer passage, put the text in a UTF-8 file:

```bash
{baseDir}/scripts/synthesize.py --input-file script.txt --out narration.wav
```

Useful options:

```bash
{baseDir}/scripts/synthesize.py "A little faster." --out faster.wav --speed 1.15
{baseDir}/scripts/synthesize.py "Save an MP3." --out speech.mp3 --format mp3
{baseDir}/scripts/synthesize.py "Use a different speaker." --out speech.wav --voice Bob
```

## Configuration

- `TTS_BASE_URL` optionally overrides the API base immediately above
  `/audio/speech`. It defaults to `http://chatterbox-tts:8000/v1`.
- `TTS_MODEL` optionally changes the default model. If unset, the script uses
  `chatterbox`.
- `TTS_VOICE` optionally changes the default voice. If unset, the script uses
  `Alice`.
- `--model` and `--voice` override those environment defaults for one request.

The client writes to a temporary file and replaces the requested output only
after a successful response, so an API failure cannot leave a partial audio
file behind.
