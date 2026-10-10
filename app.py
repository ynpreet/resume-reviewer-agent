#!/usr/bin/env python3
"""Resume Reviewer AI -- localhost preview of the static web app (stdlib only).

Run:  python3 app.py   then open http://localhost:8009/resume-reviewer.html
Serves the web/ directory (the exact files deployed to GitHub Pages) so you
can test the real client-side flow -- PDF/DOCX parsing, 33 rules, JD match --
before deploying. If port 8009 is taken, the server exits; stop the other
copy first.

Note: PDF.js and mammoth.js load from CDN, so the preview needs internet
for those two scripts. The rule engine itself is 100% local.
"""

import functools
import http.server
import sys
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8009
HERE = Path(__file__).resolve().parent
WEB = HERE / "web"


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(WEB))
    try:
        with http.server.ThreadingHTTPServer((HOST, PORT), handler) as srv:
            print("Resume Reviewer AI -- static preview")
            print("Open in Chrome: http://localhost:%d/resume-reviewer.html" % PORT)
            print("Serving: %s  (Ctrl+C to stop)" % WEB)
            srv.serve_forever()
    except OSError as exc:
        print("Port %d is already in use -- stop the other copy first. (%s)"
              % (PORT, exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
