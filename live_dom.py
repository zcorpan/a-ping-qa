# Load each page headless, wait, and record the elements carrying a ping attribute in the final DOM
# of every frame (WebDriver switches into cross-origin frames too). No clicks, so no pings are sent.
# Records token counts and ping hosts only (no full URLs, which carry tracking IDs).
# Usage: .venv/bin/python -I live_dom.py chrome data/live-pages.jsonl OUT.jsonl [WORKERS]
#   (Gecko: live_dom_gecko.py)
import json, sys, threading, time
from urllib.parse import urlsplit

from selenium import webdriver

CHROME = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
WAIT = 8
VISIT_TIMEOUT = 90

COLLECT_JS = r'''
const out = {frame_host: location.hostname, n_links: document.links.length,
             ping_idl: 'ping' in HTMLAnchorElement.prototype, elements: []};
for (const el of document.querySelectorAll('[ping]')) {
  const v = el.getAttribute('ping') || '';
  const toks = v.split(/[\t\n\f\r ]+/).filter(Boolean);
  const hosts = [], same = [], schemes = [];
  for (const t of toks) {
    try { const u = new URL(t, document.baseURI); hosts.push(u.hostname); schemes.push(u.protocol);
          same.push(u.origin === location.origin); }
    catch (e) { hosts.push(null); schemes.push(null); same.push(null); }
  }
  let href = el.getAttribute('href') ?? el.getAttributeNS('http://www.w3.org/1999/xlink', 'href');
  let hrefScheme = null;
  try { hrefScheme = href === null ? null : new URL(href, document.baseURI).protocol; } catch (e) {}
  out.elements.push({tag: el.localName, ns: el.namespaceURI, ntokens: toks.length, hosts, same, schemes,
                     href_scheme: hrefScheme, hidden: el.getClientRects().length === 0});
}
return out;
'''


def make_driver_chrome():
    o = webdriver.ChromeOptions()
    o.binary_location = CHROME
    o.add_argument('--headless=new')
    o.add_argument('--window-size=1366,900')
    o.add_argument('--no-first-run')
    o.page_load_strategy = 'eager'
    return webdriver.Chrome(options=o)


def collect(d, depth=0):
    frames = []
    try:
        frames.append(d.execute_script(COLLECT_JS))
    except Exception as e:  # noqa: BLE001
        frames.append({'error': type(e).__name__})
    if depth >= 2:
        return frames
    try:
        n = len(d.find_elements('css selector', 'iframe, frame'))
    except Exception:  # noqa: BLE001
        return frames
    for i in range(min(n, 30)):
        try:
            d.switch_to.frame(d.find_elements('css selector', 'iframe, frame')[i])
            frames += collect(d, depth + 1)
        except Exception:  # noqa: BLE001
            pass
        finally:
            try:
                d.switch_to.parent_frame()
            except Exception:  # noqa: BLE001
                pass
    return frames


def visit(d, url):
    d.set_page_load_timeout(40)
    try:
        d.get(url)
    except Exception as e:  # noqa: BLE001
        if 'timeout' not in type(e).__name__.lower():
            return {'error': type(e).__name__}
    time.sleep(WAIT)
    final = urlsplit(d.current_url).hostname
    return {'final_host': final, 'frames': collect(d)}


def kill_tree(pid):
    """Kill a process and all its descendants (driver plus the browser it started)."""
    import os, signal, subprocess
    rows = subprocess.run(['ps', '-axo', 'pid=,ppid='], capture_output=True, text=True).stdout.split()
    children = {}
    for a, b in zip(rows[::2], rows[1::2]):
        children.setdefault(int(b), []).append(int(a))
    todo, seen = [pid], []
    while todo:
        x = todo.pop()
        seen.append(x)
        todo += children.get(x, [])
    for x in seen:
        try:
            os.kill(x, signal.SIGKILL)
        except ProcessLookupError:
            pass


def close(d):
    pid = d.service.process.pid
    t = threading.Thread(target=lambda: d.quit(), daemon=True)
    t.start()
    t.join(20)
    kill_tree(pid)  # whatever quit() left behind


def run(factory, pages_path, out_path, workers):
    pages = [json.loads(l) for l in open(pages_path)]
    done = set()
    try:
        for l in open(out_path):
            r = json.loads(l)
            if 'error' not in r:
                done.add(r['url'])
    except FileNotFoundError:
        pass
    todo = [p for p in pages if p['url'] not in done]
    print(len(todo), 'to visit', flush=True)
    lock = threading.Lock()
    out = open(out_path, 'a')
    it = iter(todo)

    def worker():
        d = None
        while True:
            with lock:
                p = next(it, None)
            if p is None:
                break
            rec = {'url': p['url'], 'source': p['source']}
            try:
                if d is None:
                    d = factory()
                watchdog = threading.Timer(VISIT_TIMEOUT, kill_tree, [d.service.process.pid])
                watchdog.start()
                try:
                    rec |= visit(d, p['url'])
                finally:
                    watchdog.cancel()
            except Exception as e:  # noqa: BLE001
                rec['error'] = type(e).__name__
                if d is not None:
                    close(d)
                d = None
            with lock:
                out.write(json.dumps(rec) + '\n')
                out.flush()
            n = sum(len(f.get('elements', [])) for f in rec.get('frames', []))
            print(p['url'][:70], rec.get('error') or n, flush=True)
        if d is not None:
            close(d)

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == '__main__':
    run(make_driver_chrome, sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 2)
