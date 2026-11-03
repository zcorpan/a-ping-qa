# Local server for <a ping> tests. Serves browser/ (test.html, landing) and logs every request to
# /ping/* as one JSON line on stdout-backed log (method, path, headers that matter).
# Usage: python3 -I browser/ping_server.py 18431 18432   (listens on all given ports)
import json, os, sys, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = []
LOCK = threading.Lock()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body=b'', ctype='text/plain'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _ping(self):
        n = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(n) if n else b''
        rec = {'t': time.time(), 'method': self.command, 'host': self.headers.get('Host'), 'path': self.path,
               'ping_to': self.headers.get('Ping-To'), 'ping_from': self.headers.get('Ping-From'),
               'origin': self.headers.get('Origin'), 'referer': self.headers.get('Referer'),
               'ctype': self.headers.get('Content-Type'), 'body': body.decode('latin-1')[:20]}
        with LOCK:
            LOG.append(rec)
        if '/slow' in self.path:  # keep requests in flight, like a slow tracking endpoint
            time.sleep(0.5)
        self._send(204)

    def do_POST(self):
        if self.path.startswith('/ping/'):
            return self._ping()
        self._send(404)

    def do_GET(self):
        if self.path.startswith('/ping/'):
            return self._ping()
        if self.path.startswith('/log'):
            with LOCK:
                body = json.dumps(LOG).encode()
            return self._send(200, body, 'application/json')
        if self.path.startswith('/clear'):
            with LOCK:
                LOG.clear()
            return self._send(200, b'ok')
        if self.path.startswith('/landing'):
            return self._send(200, b'<!doctype html><title>landing</title>landing', 'text/html')
        name = self.path.split('?')[0].lstrip('/') or 'test.html'
        p = os.path.join(ROOT, os.path.basename(name))
        if os.path.isfile(p):
            with open(p, 'rb') as f:
                return self._send(200, f.read(), 'text/html; charset=utf-8')
        self._send(404)


def main():
    servers = [ThreadingHTTPServer(('', int(p)), H) for p in sys.argv[1:]]
    for s in servers[1:]:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    servers[0].serve_forever()


if __name__ == '__main__':
    main()
