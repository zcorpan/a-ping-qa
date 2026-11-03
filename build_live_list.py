# Pages to load live: HTTP Archive 10k pages with ping markup or a script that sets ping on links,
# plus Common Crawl pages with ping markup or an inline script that does.
# Usage: python3 -I build_live_list.py crawl/ha-10k.jsonl data/ha-elements.jsonl data/cc-hits.jsonl data/live-pages.jsonl
import json, re, sys
from urllib.parse import urlsplit

KINDS = {
    'setAttribute': re.compile(r'''setAttribute(?:NS)?\([^()]{0,40}["']ping["']''', re.I),
    'jquery_attr': re.compile(r'''\.(?:attr|prop)\(\s*["']ping["']'''),
    'in_check': re.compile(r'''["']ping["']\s+in\s'''),
    'markup_string': re.compile(r'''<a\b[^<>]{0,300}?\bping\s*=\s*\\?["']''', re.I),
}
# prop_set (`x.ping = ...`) hits that set it on a link element, by script URL substring.
ANCHOR_PROP_SET = ('rtct_adp_lib', 'cfnimg.joyclub.de', 'xjs/_/js/k=xjs.')
NOT_LINKS = ('cdn.cookielaw.org', 'cookie-cdn.cookiepro.com')  # `.ping = "ping"` enum, not markup


def script_kind(r):
    """Pattern kind if this non-HTML response sets ping on links, else None."""
    if r['type'] == 'html' or any(n in r['url'] for n in NOT_LINKS):
        return None
    for s in r.get('snippets') or []:
        kind = next((k for k, rx in KINDS.items() if rx.search(s)), None)
        if kind is None and re.search(r'\.ping\s*=[^=]', s) and any(n in r['url'] for n in ANCHOR_PROP_SET):
            kind = 'prop_set'
        if kind:
            return kind
    return None


def main():
    ha, ha_els, cc, out = sys.argv[1:5]
    pages = {}

    def add(url, source, reason, rank=None):
        p = pages.setdefault(url, {'url': url, 'source': source, 'rank': rank, 'reasons': []})
        if reason not in p['reasons']:
            p['reasons'].append(reason)

    for line in open(ha_els):
        r = json.loads(line)
        add(r['page'], 'httparchive', 'markup', r['rank'])
    for line in open(ha):
        r = json.loads(line)
        if script_kind(r):
            add(r['page'], 'httparchive', f"script:{urlsplit(r['url']).hostname}", r['rank'])
    for line in open(cc):
        r = json.loads(line)
        if r.get('elements'):
            add(r['url'], 'commoncrawl', 'markup')
        elif any(j['kind'] == 'markup_string' for j in r.get('js', [])):
            add(r['url'], 'commoncrawl', 'inline-script')
    with open(out, 'w') as f:
        for p in sorted(pages.values(), key=lambda p: (p['source'], p['url'])):
            f.write(json.dumps(p) + '\n')
    print(len(pages), 'pages')


if __name__ == '__main__':
    main()
