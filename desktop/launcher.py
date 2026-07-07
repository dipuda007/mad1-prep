"""MAD-1 Prep desktop launcher.

One exe that:
  1. serves the bundled prep-app pages on localhost and opens your browser
  2. has a settings page (/_settings) with "Check for updates" — pulls the
     latest content from the GitHub repo so a new term's changes reach you
     without reinstalling. Updated content is stored in %LOCALAPPDATA%\\MAD1Prep.

Build (from repo root):  powershell -File desktop/build_exe.ps1
"""

import io
import json
import os
import shutil
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

APP_NAME = "MAD-1 Prep"
VERSION = "1.1.0"
REPO = "dipuda007/mad1-prep"
BRANCH = "main"
PORT_RANGE = range(8137, 8147)

APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "MAD1Prep")
CONTENT_DIR = os.path.join(APP_DIR, "content")
META_FILE = os.path.join(APP_DIR, "meta.json")

# extensions that count as app content when applying an update
CONTENT_EXTS = (".html", ".css", ".js", ".png", ".ico", ".svg", ".gif")


def bundled_dir():
    if getattr(sys, "frozen", False):  # running as PyInstaller exe
        return os.path.join(sys._MEIPASS, "content")
    # running as plain script from desktop/ — serve the repo root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def active_dir():
    """Serve updated content if an update was ever applied, else the bundled copy."""
    if os.path.isfile(os.path.join(CONTENT_DIR, "index.html")):
        return CONTENT_DIR
    return bundled_dir()


def read_meta():
    try:
        with io.open(META_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_meta(meta):
    os.makedirs(APP_DIR, exist_ok=True)
    with io.open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f)


def github_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": APP_NAME,
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def latest_remote_sha():
    data = github_json("https://api.github.com/repos/%s/commits/%s" % (REPO, BRANCH))
    return data["sha"]


def apply_update():
    """Download the repo zip and copy the app pages into CONTENT_DIR."""
    url = "https://codeload.github.com/%s/zip/refs/heads/%s" % (REPO, BRANCH)
    req = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
    with urllib.request.urlopen(req, timeout=60) as r:
        blob = r.read()
    os.makedirs(CONTENT_DIR, exist_ok=True)
    count = 0
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for name in z.namelist():
            # entries look like "mad1-prep-app-main/index.html"
            parts = name.split("/", 1)
            if len(parts) != 2 or not parts[1] or "/" in parts[1]:
                continue  # only files at the repo root (the app is flat)
            fname = parts[1]
            if not fname.lower().endswith(CONTENT_EXTS):
                continue
            with z.open(name) as src, open(os.path.join(CONTENT_DIR, fname), "wb") as dst:
                shutil.copyfileobj(src, dst)
            count += 1
    return count


SETTINGS_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>App Settings — MAD-1 Prep</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{ font-family: "Segoe UI", Arial, sans-serif; background: #0b0f0c; color: #e6e6e6;
       max-width: 620px; margin: 40px auto; padding: 0 16px; line-height: 1.7; }}
h1 {{ color: #4ade80; }}
.card {{ background: #131a15; border: 1px solid #234; border-radius: 10px; padding: 18px 20px; margin: 14px 0; }}
button {{ background: #14532d; color: #fff; border: 0; border-radius: 8px;
          padding: 10px 20px; font-size: 15px; cursor: pointer; }}
button:hover {{ background: #1e6b3a; }}
a {{ color: #6ee7a0; }}
.msg {{ border-left: 4px solid #4ade80; padding: 8px 12px; background: #0f1a12; }}
.err {{ border-left-color: #ef4444; background: #1a0f0f; }}
small {{ color: #9aa39d; }}
</style></head><body>
<h1>⚙️ MAD-1 Prep — App Settings</h1>
{message}
<div class="card">
  <strong>App version:</strong> {version}<br>
  <strong>Content source:</strong> {source}<br>
  <strong>Last update check:</strong> {checked}<br>
  <small>Updates come from github.com/{repo} — when the project changes next
  term, the repo gets updated and this app pulls the new lessons.</small>
</div>
<div class="card">
  <form method="POST" action="/_update"><button>🔄 Check for updates</button></form>
</div>
<div class="card">
  <form method="POST" action="/_quit"><button style="background:#7f1d1d">⏻ Quit MAD-1 Prep</button></form>
</div>
<p><a href="/index.html">← Back to the app</a></p>
</body></html>"""


def settings_html(message=""):
    meta = read_meta()
    src = "updated copy (%s)" % CONTENT_DIR if active_dir() == CONTENT_DIR else "built-in copy (inside the exe)"
    return SETTINGS_PAGE.format(
        message=message, version=VERSION, source=src,
        checked=meta.get("checked", "never"), repo=REPO,
    ).encode("utf-8")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=active_dir(), **kwargs)

    def log_message(self, fmt, *args):  # keep the console clean
        pass

    def _send_html(self, body, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/_ping":
            self._send_html(b"ok")
        elif self.path.startswith("/_settings"):
            self._send_html(settings_html())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/_quit":
            self._send_html(b"<h2 style='font-family:sans-serif'>MAD-1 Prep closed. "
                            b"You can close this tab.</h2>")
            threading.Timer(0.3, lambda: os._exit(0)).start()
        elif self.path == "/_update":
            meta = read_meta()
            meta["checked"] = time.strftime("%Y-%m-%d %H:%M")
            try:
                remote = latest_remote_sha()
                if remote == meta.get("sha"):
                    write_meta(meta)
                    msg = '<div class="msg">✅ You already have the latest content.</div>'
                else:
                    n = apply_update()
                    meta["sha"] = remote
                    write_meta(meta)
                    msg = ('<div class="msg">🎉 Updated! %d files downloaded. '
                           '<a href="/index.html">Open the app</a> and refresh any open tabs.</div>' % n)
            except Exception as e:
                write_meta(meta)
                msg = ('<div class="msg err">❌ Could not fetch updates: %s.<br>'
                       'Check your internet connection (or the repo may be private).</div>' % e)
            self._send_html(settings_html(msg))
        else:
            self.send_error(404)


def find_port():
    for port in PORT_RANGE:
        # if a previous MAD1-Prep is already running, just reuse it
        try:
            req = urllib.request.Request("http://127.0.0.1:%d/_ping" % port,
                                         headers={"User-Agent": APP_NAME})
            with urllib.request.urlopen(req, timeout=0.4) as r:
                if r.read() == b"ok":
                    return port, True
        except Exception:
            pass
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port, False
    raise RuntimeError("No free port found in %s" % list(PORT_RANGE))


def main():
    port, already_running = find_port()
    url = "http://127.0.0.1:%d/index.html" % port
    if already_running:
        print("%s is already running — opening your browser." % APP_NAME)
        webbrowser.open(url)
        return
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("=" * 56)
    print(" %s v%s" % (APP_NAME, VERSION))
    print(" Running at: %s" % url)
    print(" Keep this window open while studying.")
    print(" Close it (or press Ctrl+C) to quit.")
    print("=" * 56)
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBye! Go pass that viva.")


if __name__ == "__main__":
    main()
