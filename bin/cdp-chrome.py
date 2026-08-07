#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Launch (or reuse) a remote-debugging Chrome with a named, persistent profile
on this machine (desktop-linux) or on m2book over Tailscale+SSH.

The point is stable, per-machine *named profiles*: a profile keeps its cookies
and logged-in sessions across runs, so e.g. a `banking` profile stays signed in
to Rogers/Wealthsimple and CDP automation skips the login/OTP wall. The same
profile name always maps to the same user-data-dir and the same CDP port on a
given host, so tools can just ask for `--profile banking` and attach.

    cdp-chrome.py                              # local, profile "default", :9222
    cdp-chrome.py --profile banking            # local named profile
    cdp-chrome.py --host m2book --profile banking
    cdp-chrome.py --profile banking --url https://selfserve.rogersbank.com

On success it prints the locally-reachable CDP endpoint (for m2book, via an
`ssh -L` tunnel) so a caller can `playwright.chromium.connect_over_cdp(<it>)`.
Idempotent: if CDP already answers on the target port it is reused as-is.

This is a generic launcher. Project-specific profile bootstrapping (e.g. the
actual-importer agents profile) stays in that project's own chrome_agent.py.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.request
import zlib
from pathlib import Path

LINUX_CHROME = "/usr/bin/google-chrome"
MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Local (desktop-linux) COSMIC/Wayland session details. Chrome launched without
# a session (SSH/cron) can't find the desktop, and its Wayland/EGL path
# black-screens on this NVIDIA box — force XWayland. Mirrors the hard-won
# ceremony in actual-importer/scripts/chrome/chrome_agent.py; overridable by env.
LOCAL_RUNTIME_DIR = os.environ.get("CDP_CHROME_XDG_RUNTIME_DIR", "/run/user/1000")
LOCAL_WAYLAND_SOCKET = os.environ.get("CDP_CHROME_WAYLAND_DISPLAY", "wayland-1")
LOCAL_XWAYLAND_DISPLAY = os.environ.get("CDP_CHROME_DISPLAY", ":0")


def profile_port(profile: str) -> int:
    """Deterministic per-profile CDP port so a name always lands on one port."""
    if profile == "default":
        return 9222
    return 9223 + (zlib.crc32(profile.encode()) % 60)


def cdp_up(port: int, *, host: str = "127.0.0.1", timeout: float = 1.5) -> dict | None:
    url = f"http://{host}:{port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status == 200:
                return json.loads(response.read().decode(errors="replace"))
    except Exception:  # noqa: BLE001
        return None
    return None


def wait_cdp(port: int, *, host: str = "127.0.0.1", timeout: float) -> dict | None:
    deadline = time.monotonic() + timeout
    while True:
        payload = cdp_up(port, host=host)
        if payload:
            return payload
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.4)


# ── local (desktop-linux) ────────────────────────────────────────────────────


def local_session_env() -> dict[str, str]:
    env = os.environ.copy()
    env["XDG_RUNTIME_DIR"] = LOCAL_RUNTIME_DIR
    env["WAYLAND_DISPLAY"] = LOCAL_WAYLAND_SOCKET
    env["DISPLAY"] = LOCAL_XWAYLAND_DISPLAY
    env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={LOCAL_RUNTIME_DIR}/bus"
    env["XDG_CURRENT_DESKTOP"] = "COSMIC"
    return env


def local_profile_dir(profile: str) -> Path:
    return Path.home() / ".local" / "share" / "cdp-chrome" / profile


def launch_local(profile: str, port: int, url: str, extra: list[str]) -> None:
    if not Path(LINUX_CHROME).exists():
        raise RuntimeError(f"{LINUX_CHROME} not found — is google-chrome installed?")
    profile_dir = local_profile_dir(profile)
    profile_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        LINUX_CHROME,
        "--ozone-platform=x11",
        "--new-window",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        url,
        *extra,
    ]
    log = profile_dir / "cdp-chrome.log"
    with open(log, "ab") as handle:
        subprocess.Popen(
            cmd,
            env=local_session_env(),
            stdout=handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )


def ensure_local(profile: str, port: int, url: str, extra: list[str]) -> str:
    if cdp_up(port):
        return f"http://127.0.0.1:{port}"
    launch_local(profile, port, url, extra)
    if not wait_cdp(port, timeout=20.0):
        raise RuntimeError(
            f"Chrome launched but CDP did not come up on 127.0.0.1:{port}; "
            f"check {local_profile_dir(profile) / 'cdp-chrome.log'}."
        )
    return f"http://127.0.0.1:{port}"


# ── remote (m2book over Tailscale+SSH) ───────────────────────────────────────


def ssh(host: str, command: str, *, timeout: int = 25, check: bool = True) -> str:
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", host, command],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"ssh {host} failed ({result.returncode}): {detail}")
    return result.stdout.strip()


def ensure_remote_chrome(host: str, profile: str, port: int, url: str, extra: list[str]) -> None:
    """Ensure Chrome CDP is running on the remote host (probe, else launch)."""
    probe = ssh(
        host,
        f"curl -sf http://127.0.0.1:{port}/json/version >/dev/null 2>&1 && echo up || echo down",
        check=False,
    )
    if probe.endswith("up"):
        return
    # macOS profile dir; keep named profiles under Application Support.
    profile_dir = f"$HOME/Library/Application Support/cdp-chrome/{profile}"
    extra_str = " ".join(shlex.quote(flag) for flag in extra)
    # Build the remote launch command explicitly (mkdir + nohup Chrome).
    launch = (
        f'mkdir -p "{profile_dir}" && '
        f"nohup '{MAC_CHROME}' "
        f"--user-data-dir=\"{profile_dir}\" "
        f"--no-first-run --no-default-browser-check "
        f"--remote-debugging-port={port} --remote-allow-origins=* "
        f"{shlex.quote(url)} {extra_str} "
        f">/tmp/cdp-chrome-{profile}.log 2>&1 &"
    )
    ssh(host, launch, check=False)
    # Poll the remote port from the remote side.
    for _ in range(40):
        probe = ssh(
            host,
            f"curl -sf http://127.0.0.1:{port}/json/version >/dev/null 2>&1 && echo up || echo down",
            check=False,
        )
        if probe.endswith("up"):
            return
        time.sleep(0.5)
    raise RuntimeError(
        f"Launched Chrome on {host} but its CDP did not come up on port {port}; "
        f"check /tmp/cdp-chrome-{profile}.log on {host}."
    )


def ensure_tunnel(host: str, port: int) -> None:
    """Ensure a local->remote CDP tunnel exists (idempotent)."""
    if cdp_up(port):
        return
    # -f: background after auth; -N: no remote command; keepalives so it survives idle.
    subprocess.run(
        [
            "ssh", "-f", "-N",
            "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=120",
            "-L", f"{port}:127.0.0.1:{port}",
            host,
        ],
        check=True,
        timeout=15,
    )
    if not wait_cdp(port, timeout=10.0):
        raise RuntimeError(f"CDP tunnel to {host}:{port} did not become reachable on 127.0.0.1:{port}")


def ensure_remote(host: str, profile: str, port: int, url: str, extra: list[str]) -> str:
    ensure_remote_chrome(host, profile, port, url, extra)
    ensure_tunnel(host, port)
    return f"http://127.0.0.1:{port}"


# ── main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--host",
        default="local",
        help="Where to launch: 'local'/'desktop-linux' (this machine) or 'm2book' (SSH). Default local.",
    )
    parser.add_argument("--profile", default="default", help="Named, persistent profile (default 'default').")
    parser.add_argument("--port", type=int, default=None, help="CDP port (default: derived from profile name).")
    parser.add_argument("--url", default="about:blank", help="URL to open when launching.")
    parser.add_argument("--json", action="store_true", help="Print a JSON result instead of the endpoint line.")
    parser.add_argument("extra", nargs="*", help="Extra flags passed through to Chrome.")
    args = parser.parse_args()

    port = args.port if args.port is not None else profile_port(args.profile)
    host = args.host.lower()
    local_names = {"local", "desktop-linux", "localhost", "self"}

    try:
        if host in local_names:
            endpoint = ensure_local(args.profile, port, args.url, args.extra)
            where = "desktop-linux"
        else:
            endpoint = ensure_remote(host, args.profile, port, args.url, args.extra)
            where = host
    except (RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"host": where, "profile": args.profile, "port": port, "endpoint": endpoint}))
    else:
        print(f"CDP endpoint ({where}, profile '{args.profile}'): {endpoint}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
