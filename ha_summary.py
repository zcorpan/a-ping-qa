# Summarize HTTP Archive 10k hits: pages with ping markup (parsed) and pages loading a script that
# sets ping on links, by script family, per client; plus token counts and same-origin share.
# Usage: .venv/bin/python -I ha_summary.py crawl/ha-10k.jsonl queries/pages_10k_counts.csv > data/ha-summary.md
import csv, json, os, re, sys
from collections import Counter, defaultdict
from urllib.parse import urljoin, urlsplit

from selectolax.lexbor import LexborHTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_live_list import script_kind  # noqa: E402

FAMILIES = [
    # Matched against 'script:<script host>'; rtct_adp_lib hosts are Geniee's AdPushup-derived library.
    ('AdPushup-derived ad beacon (Geniee, AdPushup, AdRecover)',
     r'script:(js\.gsspcln\.jp|js\.mediams\.mb\.softbank\.jp|js\.waqool\.com|js\.genieessp\.com|js\.ademon\.net|js\.advortex\.cloud|cdn\.adpushup\.com|delivery\.adrecover\.com)$'),
    ('Taboola Newsroom', r'script:c2\.taboola\.com$'),
    ('Google Search', r'script:www\.(google\.com(\.hk)?|gstatic\.com)$'),
    ('HubSpot login/signup UI', r'script:static\.hsappstatic\.net$'),
    ('Awin (dwin2)', r'script:www\.dwin2\.com$'),
]
WS = re.compile(r'[\t\n\f\r ]+')


def family(reason):
    for name, rx in FAMILIES:
        if re.search(rx, reason):
            return name
    return 'Other (one site each)'


def main():
    ha, counts = sys.argv[1:3]
    denom = {r['client']: r for r in csv.DictReader(open(counts))}
    markup_pages = defaultdict(set)
    ntok = Counter()
    origin = Counter()
    els_total = 0
    for line in open(ha):
        r = json.loads(line)
        if not r.get('body'):
            continue
        tree = LexborHTMLParser(r['body'])
        found = False
        for el in tree.css('a[ping], area[ping]'):
            toks = [t for t in WS.split(el.attributes.get('ping') or '') if t]
            if not toks:
                continue
            found = True
            els_total += 1
            ntok[len(toks)] += 1
            for t in toks:
                try:
                    same = urlsplit(urljoin(r['url'], t)).netloc == urlsplit(r['url']).netloc
                except ValueError:
                    same = None
                origin['same host' if same else 'cross host' if same is False else 'invalid'] += 1
        if found:
            markup_pages[r['client']].add((r['page'], r['is_root_page']))
    fam_pages = defaultdict(lambda: defaultdict(set))
    for line in open(ha):
        r = json.loads(line)
        if script_kind(r):
            fam_pages[family('script:' + urlsplit(r['url']).hostname)][r['client']].add((r['page'], r['is_root_page']))
    print('| | desktop | mobile |\n|---|---|---|')
    print(f"| Pages in sample (root) | {denom['desktop']['pages']} ({denom['desktop']['root_pages']}) | "
          f"{denom['mobile']['pages']} ({denom['mobile']['root_pages']}) |")

    def cell(s):
        return f"{len(s)} ({sum(1 for _, root in s if root)})"
    print(f"| `<a ping>`/`<area ping>` in crawled HTML (root) | {cell(markup_pages['desktop'])} | {cell(markup_pages['mobile'])} |")
    for name, _ in FAMILIES + [('Other (one site each)', None)]:
        if name in fam_pages:
            print(f"| Script: {name} (root) | {cell(fam_pages[name]['desktop'])} | {cell(fam_pages[name]['mobile'])} |")
    print(f'\nElements with a non-empty ping in crawled HTML: {els_total}; tokens per element: '
          + ', '.join(f'{k}: {v}' for k, v in sorted(ntok.items())))
    print('Ping URL vs document host: ' + ', '.join(f'{k}: {v}' for k, v in origin.most_common()))


if __name__ == '__main__':
    main()
