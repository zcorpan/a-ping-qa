# Click links with various ping attribute values in one browser setup and record which pings the
# local server (ping_server.py on ports 18431 and 18432) received.
# Usage: .venv/bin/python -I browser/run_pings.py SETUP OUT.json
#   SETUP: chrome | chrome-mathml | safari-tp   [CASE,CASE...] to run only those cases
#    (Gecko setups: run_pings_gecko.py)
import json, sys, time, urllib.request
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BASE = 'http://localhost:18431'
CHROME = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
SAFARIDRIVER = '/Applications/Safari Technology Preview.app/Contents/MacOS/safaridriver'

COUNTS = [1, 2, 3, 4, 5, 8, 10, 16, 32, 64, 100, 128, 256, 257, 500, 1000]


def cases():
    out = []
    for n in COUNTS:
        out.append((f'n{n}', 'a', ' '.join(f'/ping/n{n}/{i}' for i in range(n)), 'native'))
    for n in (256, 257, 300, 500):  # server holds each ping 0.5 s, so the rest queue in flight
        out.append((f'slow{n}', 'a', ' '.join(f'/ping/slow{n}/{i}' for i in range(n)), 'native'))
    out += [
        ('same_abs', 'a', 'http://localhost:18431/ping/same_abs/0', 'native'),
        ('xport', 'a', 'http://localhost:18432/ping/xport/0', 'native'),
        ('xhost', 'a', 'http://127.0.0.1:18431/ping/xhost/0', 'native'),
        ('x_then_same', 'a', 'http://127.0.0.1:18431/ping/x_then_same/0 /ping/x_then_same/1', 'native'),
        ('dup', 'a', '/ping/dup/0 /ping/dup/0', 'native'),
        ('data_first', 'a', 'data:,x /ping/data_first/1', 'native'),
        ('js_first', 'a', 'javascript:void(0) /ping/js_first/1', 'native'),
        ('ftp_first', 'a', 'ftp://localhost/ping/ftp_first/0 /ping/ftp_first/1', 'native'),
        ('invalid_first', 'a', 'http://[ /ping/invalid_first/1', 'native'),
        ('ws_separators', 'a', '/ping/ws/0\n/ping/ws/1\t/ping/ws/2\f/ping/ws/3', 'native'),
        ('area', 'area', '/ping/area/0 /ping/area/1', 'native'),
        ('svg_a', 'svg_a', '/ping/svg_a/0 /ping/svg_a/1', 'native'),
        ('js_click', 'a', '/ping/js_click/0 /ping/js_click/1', 'js'),
        ('blank_target', 'a_blank', '/ping/blank/0 /ping/blank/1', 'native'),
        ('mathml_a', 'mathml_a', '/ping/mathml_a/0 /ping/mathml_a/1', 'native'),
        ('beacon_dispatch', 'beacon', '/ping/beacon_dispatch/0 /ping/beacon_dispatch/1 /ping/beacon_dispatch/2', 'beacon_dispatch'),
        ('beacon_click', 'beacon', '/ping/beacon_click/0 /ping/beacon_click/1 /ping/beacon_click/2', 'beacon_click'),
    ]
    return out


SETUP_JS = r'''
const [kind, ping, id] = arguments;
const c = document.getElementById('container');
c.textContent = '';
const href = '/landing?case=' + id;
let target;
if (kind === 'area') {
  const img = document.createElement('img');
  img.src = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="red"/></svg>');
  img.useMap = '#m'; img.width = 200; img.height = 200; img.id = 'target';
  const map = document.createElement('map'); map.name = 'm';
  const area = document.createElement('area');
  area.shape = 'rect'; area.coords = '0,0,200,200'; area.href = href; area.setAttribute('ping', ping);
  map.append(area); c.append(map, img);
  target = img;
} else if (kind === 'svg_a') {
  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('width', 200); svg.setAttribute('height', 200);
  const a = document.createElementNS(NS, 'a'); a.setAttribute('href', href); a.setAttribute('ping', ping);
  const r = document.createElementNS(NS, 'rect'); r.setAttribute('width', 200); r.setAttribute('height', 200); r.setAttribute('id', 'target');
  a.append(r); svg.append(a); c.append(svg);
} else if (kind === 'mathml_a') {
  const NS = 'http://www.w3.org/1998/Math/MathML';
  const math = document.createElementNS(NS, 'math'); math.style.fontSize = '40px';
  const a = document.createElementNS(NS, 'a'); a.setAttribute('href', href); a.setAttribute('ping', ping);
  const t = document.createElementNS(NS, 'mtext'); t.textContent = 'click me'; t.setAttribute('id', 'target');
  a.append(t); math.append(a); c.append(math);
} else if (kind === 'beacon') {
  // Ad-script pattern: hidden anchor with a javascript: href, ping set before each synthetic click.
  const a = document.createElement('a');
  a.href = 'javascript:void(0)'; a.style.display = 'none'; a.setAttribute('ping', ''); a.id = 'beacon';
  a.addEventListener('click', e => e.stopPropagation());
  const t = document.createElement('span'); t.id = 'target';
  c.append(a, t);
} else {
  const a = document.createElement('a');
  a.href = href; a.setAttribute('ping', ping); a.textContent = 'click me'; a.id = 'target';
  if (kind === 'a_blank') a.target = '_blank';
  c.append(a);
}
return document.getElementById('target') !== null;
'''


def http(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.read()


def make_driver(setup):
    if setup == 'chrome':
        o = webdriver.ChromeOptions()
        o.binary_location = CHROME
        o.add_argument('--headless=new')
        o.add_argument('--window-size=1000,800')
        o.add_argument('--no-first-run')
        return webdriver.Chrome(options=o)
    if setup == 'chrome-mathml':
        o = webdriver.ChromeOptions()
        o.binary_location = CHROME
        o.add_argument('--headless=new')
        o.add_argument('--window-size=1000,800')
        o.add_argument('--enable-blink-features=MathMLAnchorElement')
        return webdriver.Chrome(options=o)
    if setup == 'safari-tp':
        o = webdriver.SafariOptions()
        o.use_technology_preview = True
        return webdriver.Safari(options=o, service=webdriver.SafariService(executable_path=SAFARIDRIVER))
    raise SystemExit('unknown setup ' + setup)


def main(driver_factory=None):
    setup, out = sys.argv[1], sys.argv[2]
    d = (driver_factory or make_driver)(setup)
    results = {'setup': setup, 'browser': d.capabilities.get('browserName'),
               'version': d.capabilities.get('browserVersion'), 'cases': []}
    try:
        only = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else None
        for cid, kind, ping, how in cases():
            if only and cid not in only:
                continue
            d.get(BASE + '/test.html')
            http('/clear')
            assert d.execute_script(SETUP_JS, kind, ping, cid)
            handles = set(d.window_handles)
            el = d.find_element(By.ID, 'target')
            error = None
            try:
                if how.startswith('beacon'):
                    d.execute_script('''
                      const a = document.getElementById('beacon');
                      for (const u of arguments[0].split(' ')) {
                        a.setAttribute('ping', u);
                        if (arguments[1] === 'beacon_click') { a.click(); continue; }
                        const ev = document.createEvent('MouseEvent');
                        ev.initMouseEvent('click', true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
                        a.dispatchEvent(ev);
                      }''', ping, how)
                elif how == 'js':
                    d.execute_script("document.querySelector('a').click()")
                elif kind == 'area':
                    ActionChains(d).move_to_element(el).click().perform()
                else:
                    el.click()
                if kind not in ('a_blank', 'beacon'):
                    WebDriverWait(d, 10).until(lambda d: 'landing' in d.current_url)
            except Exception as e:  # noqa: BLE001
                error = type(e).__name__
            time.sleep(50 if cid.startswith('slow') else 10 if cid in ('n500', 'n1000') else 2)
            log = json.loads(http('/log'))
            for h in set(d.window_handles) - handles:
                d.switch_to.window(h)
                d.close()
            d.switch_to.window(sorted(handles)[0])
            expected = ping.split()
            results['cases'].append({'case': cid, 'kind': kind, 'click': how, 'tokens': len(expected),
                                     'received': len(log), 'error': error,
                                     'paths': [r['host'] + r['path'] for r in log][:20],
                                     'sample': log[:2]})
            print(setup, cid, len(expected), '->', len(log), error or '', flush=True)
    finally:
        d.quit()
    with open(out, 'w') as f:
        json.dump(results, f, indent=1)


if __name__ == '__main__':
    main()
