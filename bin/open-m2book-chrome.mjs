#!/usr/bin/env node
// Open a URL in a CDP-controlled Chrome instance running on m2book.
//
// Usage:  open-m2book-chrome <url>
//
// 1. SSHes into m2book (Tailscale), ensures a dedicated Chrome is
//    running with --remote-debugging-port=9223 and a temp profile.
// 2. Creates a reverse SSH tunnel so m2book can reach the local
//    HTTP server behind <url> (the pi-web-access search curator).
// 3. Uses Chrome DevTools Protocol (/json/new) to navigate to the
//    tunneled URL.
// 4. Falls back to macOS `open` if CDP fails.
//
// Designed as a drop-in replacement for xdg-open for pi-web-access's
// search-curator workflow.

import { spawnSync, spawn } from "node:child_process";
import { setTimeout as sleep } from "node:timers/promises";
import { writeFileSync } from "node:fs";

const M2BOOK   = "m2book";
const CDP_PORT = 9223;
const CHROME   = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PROFILE  = "/tmp/pi-curator-chrome";

// ── helpers ──────────────────────────────────────────────────────────

function ssh(cmd, opts = {}) {
  // cmd is a single shell string; SSH passes it via the remote shell
  const r = spawnSync("ssh", [
    "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
    M2BOOK, cmd,
  ], { encoding: "utf-8", timeout: 25_000, stdio: ["ignore", "pipe", "pipe"], ...opts });
  if (r.error) throw r.error;
  if (r.status !== 0 && !opts.allowFailure) {
    const msg = (r.stderr || r.stdout || "").trim();
    throw new Error(`ssh exited ${r.status}: ${msg}`);
  }
  return r.stdout.trim();
}

let tunnelProc = null;

function sshDetach(tunnelArgs) {
  // Fire-and-forget SSH with both tunnels; keeps running in background.
  const all = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
               "-o", "ExitOnForwardFailure=yes",
               "-o", "ServerAliveInterval=15",
               "-o", "ServerAliveCountMax=20",     // ~5 min idle timeout
               "-N",                              // no remote command
               M2BOOK, ...tunnelArgs];
  const p = spawn(all[0], all.slice(1), {
    stdio: ["ignore", "pipe", "pipe"],
  });
  p.unref();
  tunnelProc = p;

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      p.removeListener("exit", onExit);
      resolve();
    }, 2000);

    const onExit = (code, sig) => {
      clearTimeout(timer);
      if (code !== 0 && code !== null) {
        const stderr = p.stderr.read() || "";
        reject(new Error(`SSH tunnel exited ${code}: ${stderr}`));
      } else {
        resolve();
      }
    };
    p.on("exit", onExit);
    p.on("error", (err) => { clearTimeout(timer); reject(err); });
  });
}

// ── ensure Chrome CDP on m2book ──────────────────────────────────────

async function ensureChromeCdp() {
  // Check if Chrome with CDP is already running
  try {
    const out = ssh(`lsof -ti :${CDP_PORT} 2>/dev/null`, { allowFailure: true });
    if (out) {
      console.error(`Chrome CDP already running (pid ${out.trim()})`);
      return;
    }
  } catch { /* not running */ }

  console.error("Starting Chrome with CDP on m2book…");
  // Shell-quoted command string run over SSH
  const launchCmd =
    `nohup '${CHROME}' ` +
    `--remote-debugging-port=${CDP_PORT} ` +
    `--user-data-dir='${PROFILE}' ` +
    `--no-first-run --no-default-browser-check --disable-fre ` +
    `>/tmp/pi-curator-chrome.log 2>&1 &`;
  spawnSync("ssh", [
    "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
    M2BOOK, launchCmd,
  ], { encoding: "utf-8", timeout: 10_000, stdio: ["ignore", "pipe", "pipe"] });

  await sleep(3000);

  // Verify it started
  try {
    const pid = ssh(`lsof -ti :${CDP_PORT} 2>/dev/null`, { allowFailure: true });
    if (pid) {
      console.error(`Chrome CDP ready (pid ${pid.trim()})`);
    } else {
      console.error("Warning: Chrome CDP may not have started on m2book");
    }
  } catch {
    console.error("Warning: Chrome CDP may not have started on m2book");
  }
}

// ── main ─────────────────────────────────────────────────────────────

async function main() {
  const url = process.argv[2];
  if (!url) {
    console.error("Usage: open-m2book-chrome <url>");
    process.exit(1);
  }

  const parsed = new URL(url);
  const curatorPort = parseInt(parsed.port, 10);
  if (!curatorPort || parsed.hostname !== "localhost") {
    console.error(`Expected localhost curator URL, got: ${url}`);
    process.exit(1);
  }

  const pathQuery = parsed.pathname + parsed.search;

  // 1. Ensure Chrome with CDP is running on m2book
  await ensureChromeCdp();

  console.error("Opening curator on m2book…");

  // 2. Set up dual tunnels via a single background SSH:
  //    -L <CDP_PORT>:localhost:<CDP_PORT>
  //        → makes m2book's CDP port reachable on our localhost:<CDP_PORT>
  //    -R <curatorPort>:localhost:<curatorPort>
  //        → makes our local curator reachable on m2book's localhost:<curatorPort>
  const cdpFwd     = `${CDP_PORT}:localhost:${CDP_PORT}`;
  const curatorRev = `${curatorPort}:localhost:${curatorPort}`;
  const tunnelUrl  = `http://localhost:${curatorPort}${pathQuery}`;

  // Start background SSH with both tunnels (-N = no remote command)
  try {
    sshDetach(["-L", cdpFwd, "-R", curatorRev]);
    console.error("SSH tunnels established");
  } catch (err) {
    console.error(`SSH tunnel failed: ${err.message}`);
    console.error(`Open manually on m2book: ${url}`);
    process.exit(1);
  }

  // Give tunnels a moment
  await sleep(1000);

  // 3. Navigate via CDP (http://localhost:<CDP_PORT>/json/new?url=...)
  try {
    const script =
      `curl -sf "http://localhost:${CDP_PORT}/json/new?url=` +
      `${encodeURIComponent(tunnelUrl)}"`;
    const out = ssh(script, { timeout: 10_000 });
    const info = JSON.parse(out);
    console.error(`Tab opened: ${info.title || info.id || "ok"}`);
  } catch (err) {
    console.error(`CDP navigation failed: ${err.message}`);
    // Fallback: reverse tunnel + macOS open
    try {
      console.error("Falling back to macOS open…");
      ssh(`sleep 1 && open '${tunnelUrl}'`, { timeout: 15_000 });
      console.error("URL opened via macOS open command");
    } catch (err2) {
      console.error(`Fallback also failed: ${err2.message}`);
      console.error(`Open this URL in Chrome on m2book: ${tunnelUrl}`);
    }
  }
}

// Persist tunnel PID so a cleanup cron/daemon can reap it later.
// The tunnel self-terminates after ~5 min of idle (ServerAlive settings).
const PIDFILE = "/tmp/pi-curator-tunnel.pid";

main().then(() => {
  // Write tunnel PID for cleanup if desired
  if (tunnelProc && tunnelProc.pid) {
    try { writeFileSync(PIDFILE, String(tunnelProc.pid) + "\n"); } catch {}
  }
  setImmediate(() => process.exit(0));
}).catch((err) => {
  console.error(`open-m2book-chrome failed: ${err.message}`);
  process.exit(1);
});
