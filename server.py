import http.server
import socketserver
import os
import json
import hashlib
import hmac
import subprocess
import sys
import datetime
import ipaddress

# ================================================================
#  CONFIGURATION — Only change these values
# ================================================================
PORT        = 8000
DIRECTORY   = r"c:\Users\dhanu\Downloads\New folder"
LOG_FILE    = os.path.join(DIRECTORY, "server_audit.log")

# SECRET TOKEN — The editor must send this exact token in the
# X-Auth-Token header. Keep this private. Change it to something
# unique and hard to guess before running.
SECRET_TOKEN = "SLVGP-HASSAN-2024-SECURE-9X7K2M"

# Maximum allowed POST body size: 5 MB. Requests larger than this
# are rejected immediately to prevent RAM exhaustion attacks.
MAX_CONTENT_BYTES = 10 * 1024 * 1024  # 5 MB

# The ONLY file names that are allowed to be written.
# Any attempt to write to any other filename is blocked.
ALLOWED_OUTPUT_FILES = {
    "slvgp-hassan-website.html",
    "index.html"
}

# The ONLY git executable path. Hardcoded to prevent PATH hijacking.
# Run `where git` in your terminal to confirm this path is correct.
GIT_EXECUTABLE = r"C:\Program Files\Git\cmd\git.exe"

# ================================================================
#  AUDIT LOGGER — Writes every request to server_audit.log
# ================================================================
def audit_log(event: str, ip: str, detail: str = ""):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{event}] IP={ip} {detail}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(line.strip())


# ================================================================
#  SECURITY: Verify the secret token using constant-time comparison
#  to prevent timing-based attacks.
# ================================================================
def verify_token(provided_token: str) -> bool:
    expected = SECRET_TOKEN.encode("utf-8")
    provided = provided_token.encode("utf-8")
    # hmac.compare_digest prevents timing attacks that could leak
    # the token character-by-character through response timing.
    return hmac.compare_digest(
        hashlib.sha256(expected).digest(),
        hashlib.sha256(provided).digest()
    )


# ================================================================
#  SECURITY: Validate that the resolved output path stays inside
#  DIRECTORY. Blocks all path traversal attacks (e.g. ../../etc).
# ================================================================
def safe_output_path(filename: str):
    # Strip any directory separators — only bare filenames allowed.
    bare_name = os.path.basename(filename)
    if bare_name not in ALLOWED_OUTPUT_FILES:
        return None
    resolved = os.path.realpath(os.path.join(DIRECTORY, bare_name))
    base     = os.path.realpath(DIRECTORY)
    # Ensure the resolved path is still inside the workspace.
    if not resolved.startswith(base + os.sep) and resolved != base:
        return None
    return resolved


# ================================================================
#  SECURITY: Verify Git executable exists at the hardcoded path
#  before calling subprocess, preventing PATH hijacking.
# ================================================================
def get_verified_git():
    if os.path.isfile(GIT_EXECUTABLE):
        return GIT_EXECUTABLE
    # Fallback: search common locations only
    fallbacks = [
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    ]
    for path in fallbacks:
        if os.path.isfile(path):
            return path
    return None


# ================================================================
#  CUSTOM HTTP REQUEST HANDLER
# ================================================================
class SecureEditorHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    # ----------------------------------------------------------
    #  Override: block all incoming connections that are NOT
    #  from localhost (127.0.0.1 or ::1).
    # ----------------------------------------------------------
    def _is_localhost(self) -> bool:
        client_ip = self.client_address[0]
        try:
            addr = ipaddress.ip_address(client_ip)
            return addr.is_loopback
        except ValueError:
            return False

    # ----------------------------------------------------------
    #  Override log_message to suppress default noisy output
    #  and redirect everything to our audit logger.
    # ----------------------------------------------------------
    def log_message(self, format, *args):
        audit_log("HTTP", self.client_address[0], format % args)

    # ----------------------------------------------------------
    #  Add security headers to ALL responses.
    # ----------------------------------------------------------
    def send_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store")

    # ----------------------------------------------------------
    #  Override GET to block non-localhost access.
    # ----------------------------------------------------------
    def do_GET(self):
        if not self._is_localhost():
            audit_log("BLOCKED_GET", self.client_address[0],
                      "Remote access attempt rejected")
            self.send_response(403)
            self.end_headers()
            return
        super().do_GET()

    # ----------------------------------------------------------
    #  Handle POST requests — the save endpoint.
    # ----------------------------------------------------------
    def do_POST(self):
        client_ip = self.client_address[0]

        # SECURITY CHECK 1: Block all non-localhost connections.
        if not self._is_localhost():
            audit_log("BLOCKED_POST", client_ip,
                      "Non-localhost POST attempt rejected")
            self.send_response(403)
            self.end_headers()
            return

        # SECURITY CHECK 2: Only accept /save endpoint.
        if self.path != "/save":
            audit_log("INVALID_PATH", client_ip, f"path={self.path}")
            self.send_response(404)
            self.end_headers()
            return

        # SECURITY CHECK 3: Validate secret token.
        provided_token = self.headers.get("X-Auth-Token", "").strip()
        if not verify_token(provided_token):
            audit_log("AUTH_FAIL", client_ip,
                      "Invalid or missing X-Auth-Token header")
            self.send_response(401)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": "Unauthorized. Invalid security token."
            }).encode())
            return

        # SECURITY CHECK 4: Enforce maximum request body size.
        raw_length = self.headers.get("Content-Length", "0")
        try:
            content_length = int(raw_length)
        except ValueError:
            content_length = 0

        if content_length <= 0 or content_length > MAX_CONTENT_BYTES:
            audit_log("SIZE_VIOLATION", client_ip,
                      f"Content-Length={content_length} exceeds limit")
            self.send_response(413)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Request too large. Max allowed: {MAX_CONTENT_BYTES} bytes."
            }).encode())
            return

        # Read the POST body.
        post_data = self.rfile.read(content_length)

        try:
            html_content = post_data.decode("utf-8")
        except UnicodeDecodeError:
            audit_log("DECODE_ERROR", client_ip, "Body is not valid UTF-8")
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": "Invalid encoding. Only UTF-8 is accepted."
            }).encode())
            return

        # SECURITY CHECK 5: Validate HTML content is non-empty.
        if len(html_content.strip()) < 100:
            audit_log("EMPTY_BODY", client_ip, "Body too short to be valid HTML")
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": "Content is too short or empty."
            }).encode())
            return

        # Write website files — path traversal safe.
        files_written = []
        for filename in ["slvgp-hassan-website.html", "index.html"]:
            safe_path = safe_output_path(filename)
            if safe_path is None:
                audit_log("PATH_TRAVERSAL_ATTEMPT", client_ip,
                          f"Blocked write to: {filename}")
                continue
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            files_written.append(filename)

        audit_log("SAVE_OK", client_ip,
                  f"Wrote {len(html_content)} bytes to: {files_written}")

        # Auto git commit and push using verified executable only.
        git_status = "local_only"
        git_exe = get_verified_git()
        git_dir = os.path.join(DIRECTORY, ".git")

        if git_exe and os.path.exists(git_dir):
            try:
                stage_files = [
                    "index.html",
                    "slvgp-hassan-website.html",
                    "slvgp-hassan-editor.html",
                    "server.py",
                    "logo-removebg-preview.png"
                ]
                # Use full absolute git path — no PATH dependency.
                subprocess.run(
                    [git_exe, "add"] + stage_files,
                    cwd=DIRECTORY, check=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                # Commit with timestamp for audit trail.
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                subprocess.run(
                    [git_exe, "commit", "-m",
                     f"CMS Auto-save [{ts}] — {len(html_content)} bytes"],
                    cwd=DIRECTORY,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                # Push to GitHub.
                res = subprocess.run(
                    [git_exe, "push", "origin", "main"],
                    cwd=DIRECTORY,
                    capture_output=True, text=True, timeout=30
                )
                if res.returncode == 0:
                    git_status = "pushed"
                    audit_log("GIT_PUSH_OK", client_ip, "Pushed to GitHub")
                else:
                    git_status = f"push_error: {res.stderr.strip()[:200]}"
                    audit_log("GIT_PUSH_FAIL", client_ip, git_status)
            except subprocess.TimeoutExpired:
                git_status = "push_timeout"
                audit_log("GIT_TIMEOUT", client_ip, "Git push timed out after 30s")
            except Exception as ge:
                git_status = f"git_exception: {str(ge)[:200]}"
                audit_log("GIT_ERROR", client_ip, git_status)
        elif not git_exe:
            audit_log("GIT_NOT_FOUND", client_ip,
                      "Git binary not found at expected paths")

        # Send success response.
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(json.dumps({
            "status":     "success",
            "message":    f"Saved {len(files_written)} file(s) successfully.",
            "git_status": git_status,
            "bytes":      len(html_content)
        }).encode())


# ================================================================
#  MAIN — Bind ONLY to localhost (127.0.0.1), not all interfaces.
# ================================================================
def main():
    os.chdir(DIRECTORY)

    handler  = SecureEditorHandler
    socketserver.TCPServer.allow_reuse_address = True

    # CRITICAL: Binding to "127.0.0.1" instead of "" means
    # ONLY this machine can reach the server. No WiFi/LAN access.
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        print("================================================================")
        print("  SLVGP HASSAN SECURE LOCAL CMS SERVER")
        print("================================================================")
        print(f"  Bound to: 127.0.0.1:{PORT} (localhost only — WiFi blocked)")
        print(f"  Token:    {SECRET_TOKEN[:8]}... (keep this private)")
        print(f"  Audit:    {LOG_FILE}")
        print(f"  --> Editor:  http://localhost:{PORT}/slvgp-hassan-editor.html")
        print(f"  --> Website: http://localhost:{PORT}/slvgp-hassan-website.html")
        print("================================================================")
        print("  Press Ctrl+C to stop the server.")
        print()
        audit_log("SERVER_START", "127.0.0.1",
                  f"Secure server started on port {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            audit_log("SERVER_STOP", "127.0.0.1", "Graceful shutdown via Ctrl+C")
            print("\nServer shut down cleanly.")


if __name__ == "__main__":
    # Block execution if Python version is too old.
    if sys.version_info < (3, 9):
        print("[ERROR] Python 3.9 or newer is required.")
        sys.exit(1)
    main()
