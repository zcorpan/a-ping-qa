# Classify ping_10k.sql hits (downloaded with bq_download.py) locally.
# Usage: .venv/bin/python -I ha_classify.py crawl/ha-10k.jsonl data/
# Writes data/ha-elements.jsonl (one line per HTML response with elements carrying a ping
# attribute, parsed with lexbor) and data/ha-js-groups.jsonl (script snippets matching the targeted
# patterns, grouped by response URL without query string and pattern kind).
import json, re, sys
from collections import defaultdict
from urllib.parse import urljoin, urlsplit

from selectolax.lexbor import LexborHTMLParser

WS = re.compile(r'[\t\n\f\r ]+')
KINDS = {
    'setAttribute': re.compile(r'''setAttribute(?:NS)?\([^()]{0,40}["']ping["']''', re.I),
    'jquery_attr': re.compile(r'''\.(?:attr|prop)\(\s*["']ping["']'''),
    'in_check': re.compile(r'''["']ping["']\s+in\s'''),
    'markup_string': re.compile(r'''<a\b[^<>]{0,300}?\bping\s*=''', re.I),
    'prototype': re.compile(r'''prototype\.ping\b'''),
    'prop_set': re.compile(r'''\.ping\s*=[^=]'''),
    'attr_eq': re.compile(r'''\bping\s*=''', re.I),
}


def main():
    src, out = sys.argv[1], sys.argv[2]
    els_out = open(f'{out}/ha-elements.jsonl', 'w')
    groups = defaultdict(lambda: {'pages': set(), 'clients': set(), 'snippets': [], 'types': set()})
    for line in open(src):
        r = json.loads(line)
        if r.get('body'):
            tree = LexborHTMLParser(r['body'])
            base = r['url']
            b = tree.css_first('base[href]')
            if b is not None and b.attributes.get('href'):
                base = urljoin(r['url'], b.attributes['href'].strip())
            els = []
            for el in tree.css('[ping]'):
                v = el.attributes.get('ping') or ''
                toks = [t for t in WS.split(v) if t]
                res = []
                for t in toks:
                    try:
                        res.append(urljoin(base, t))
                    except ValueError:
                        res.append(None)
                els.append({'tag': el.tag, 'ping': v[:1000], 'ntokens': len(toks), 'resolved': res,
                            'href': (el.attributes.get('href') or '')[:300]})
            if els:
                els_out.write(json.dumps({k: r[k] for k in ('date', 'client', 'page', 'is_root_page', 'rank',
                                                              'url', 'type')} | {'elements': els}) + '\n')
        for s in r.get('snippets') or []:
            for kind, rx in KINDS.items():
                if rx.search(s):
                    if kind == 'attr_eq' and r['type'] == 'html':
                        break  # markup in HTML is covered by the parse above
                    u = urlsplit(r['url'])
                    key = (u.netloc + u.path, kind)
                    g = groups[key]
                    g['pages'].add(r['page'])
                    g['clients'].add(r['client'])
                    g['types'].add(r['type'])
                    if len(g['snippets']) < 3 and s not in g['snippets']:
                        g['snippets'].append(s)
                    break
    with open(f'{out}/ha-js-groups.jsonl', 'w') as f:
        for (url, kind), g in sorted(groups.items(), key=lambda kv: -len(kv[1]['pages'])):
            f.write(json.dumps({'url': url, 'kind': kind, 'pages': len(g['pages']), 'clients': sorted(g['clients']),
                                'types': sorted(g['types']), 'snippets': g['snippets']}) + '\n')


if __name__ == '__main__':
    main()
