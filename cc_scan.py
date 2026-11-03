# Scan local Common Crawl WARCs for <a ping>/<area ping> markup and inline-script use of `ping`.
# Usage: .venv/bin/python -I cc_scan.py OUT_DIR WARC...
# Writes OUT_DIR/cc-hits.jsonl (one line per page with a hit) and OUT_DIR/cc-totals.json.
# The prefilter (`ping\s*=` or a quoted "ping", case-insensitive) matches every element with a
# non-empty ping attribute, so markup recall is complete; bodies over 3 MB are skipped (cc.py).
import json, os, re, sys
from multiprocessing import Pool
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc import html_responses  # noqa: E402

PREFILTER = re.compile(r'''ping\s*=|['"]ping['"]''', re.I)
JS_PATTERNS = {
    'prop_set': re.compile(r'''\.ping\s*=(?!=)'''),
    'setAttribute': re.compile(r'''setAttribute(?:NS)?\(\s*(?:[^,()]*,\s*)?['"]ping['"]''', re.I),
    'jquery_attr': re.compile(r'''\.(?:attr|prop)\(\s*['"]ping['"]'''),
    'in_check': re.compile(r'''['"]ping['"]\s+in\s'''),
    'markup_string': re.compile(r'''<a\b[^<>]{0,300}?\bping\s*=''', re.I),
    'prototype': re.compile(r'''HTMLAnchorElement\.prototype\.ping|HTMLAreaElement\.prototype\.ping'''),
}
WS = re.compile(r'[\t\n\f\r ]+')


def tokens(v):
    return [t for t in WS.split(v) if t]


def scan_page(url, html):
    from selectolax.lexbor import LexborHTMLParser
    tree = LexborHTMLParser(html)
    base = url
    b = tree.css_first('base[href]')
    if b is not None and b.attributes.get('href'):
        base = urljoin(url, b.attributes['href'].strip())
    elements = []
    for el in tree.css('[ping]'):
        v = el.attributes.get('ping') or ''
        toks = tokens(v)
        resolved = []
        for t in toks:
            try:
                resolved.append(urljoin(base, t))
            except ValueError:
                resolved.append(None)
        elements.append({'tag': el.tag, 'ping': v[:2000], 'ntokens': len(toks),
                         'resolved': [r[:500] if r else r for r in resolved],
                         'href': (el.attributes.get('href') or '')[:500]})
    js = []
    for s in tree.css('script'):
        if s.attributes.get('src'):
            continue
        text = s.text() or ''
        if not PREFILTER.search(text) and 'prototype.ping' not in text:
            continue
        for kind, rx in JS_PATTERNS.items():
            for m in rx.finditer(text):
                a, z = max(0, m.start() - 150), min(len(text), m.end() + 150)
                js.append({'kind': kind, 'snippet': text[a:z]})
                if len(js) > 50:
                    break
    return elements, js


def scan_warc(path):
    n = pre = 0
    hits = []
    for url, html in html_responses(path):
        n += 1
        if not PREFILTER.search(html) and 'prototype.ping' not in html:
            continue
        pre += 1
        try:
            elements, js = scan_page(url, html)
        except Exception as e:  # noqa: BLE001
            hits.append({'url': url, 'warc': os.path.basename(path), 'error': repr(e)[:200]})
            continue
        if elements or js:
            hits.append({'url': url, 'warc': os.path.basename(path), 'host': urlsplit(url).hostname,
                         'elements': elements, 'js': js})
    return os.path.basename(path), n, pre, hits


def main():
    out_dir, warcs = sys.argv[1], sys.argv[2:]
    os.makedirs(out_dir, exist_ok=True)
    totals = {}
    with open(os.path.join(out_dir, 'cc-hits.jsonl'), 'w') as f, Pool(min(12, len(warcs))) as pool:
        for name, n, pre, hits in pool.imap_unordered(scan_warc, warcs):
            totals[name] = {'html_responses': n, 'prefiltered': pre, 'pages_with_hits': len(hits)}
            for h in hits:
                f.write(json.dumps(h) + '\n')
            print(name, totals[name], flush=True)
    with open(os.path.join(out_dir, 'cc-totals.json'), 'w') as f:
        json.dump(totals, f, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
