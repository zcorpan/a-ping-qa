# Summarize live_dom.py output for Chrome and Firefox: pages with ping elements in the final DOM,
# tokens per element, same-origin share, and per-page differences between the browsers.
# Usage: python3 -I analyze_live.py out/live-chrome.jsonl out/live-firefox.jsonl > data/live-summary.md
import json, sys
from collections import Counter


def load(path):
    return {r['url']: r for r in map(json.loads, open(path))}


def elements(rec):
    return [e for f in rec.get('frames', []) for e in f.get('elements', [])
            if e['tag'] in ('a', 'area') and e['ntokens'] > 0]


def summarize(name, recs):
    ok = [r for r in recs.values() if 'error' not in r]
    with_ping = [r for r in ok if elements(r)]
    els = [e for r in ok for e in elements(r)]
    ntok = Counter(e['ntokens'] for e in els)
    same = Counter('same origin' if s else 'cross origin' if s is False else 'invalid'
                   for e in els for s in e['same'])
    ns = Counter((e['tag'], (e['ns'] or '').rsplit('/', 1)[-1]) for e in els)
    hidden = sum(e['hidden'] for e in els)
    idl = Counter(f.get('ping_idl') for r in ok for f in r.get('frames', [])[:1])
    print(f'**{name}**: {len(ok)} of {len(recs)} pages loaded; {len(with_ping)} with a non-empty '
          f'`ping` on `<a>`/`<area>` in some frame; {len(els)} elements.')
    print(f'- Tokens per element: ' + ', '.join(f'{k}: {v}' for k, v in sorted(ntok.items())))
    print(f'- Ping URL vs frame origin: ' + ', '.join(f'{k}: {v}' for k, v in same.most_common()))
    print(f'- Elements by tag and namespace: ' + ', '.join(f'{t} ({n}): {v}' for (t, n), v in ns.most_common()))
    print(f'- Hidden (no client rects): {hidden}')
    print(f"- `'ping' in HTMLAnchorElement.prototype` in the top frame: " + ', '.join(f'{k}: {v}' for k, v in idl.items()))
    hosts = Counter(h for e in els for h, s in zip(e['hosts'], e['same']) if s is False)
    print(f'- Cross-origin ping hosts: ' + ', '.join(f'`{h}`: {v}' for h, v in hosts.most_common(10)))
    print()


def main():
    chrome, firefox = load(sys.argv[1]), load(sys.argv[2])
    summarize('Chrome Canary', chrome)
    summarize('Firefox Nightly (send_pings on, max_per_link=-1)', firefox)
    diffs = []
    for url in sorted(set(chrome) & set(firefox)):
        c, f = chrome[url], firefox[url]
        if 'error' in c or 'error' in f:
            continue
        ce, fe = elements(c), elements(f)
        if len(ce) != len(fe) or sorted(e['ntokens'] for e in ce) != sorted(e['ntokens'] for e in fe):
            diffs.append((url, len(ce), len(fe), max([e['ntokens'] for e in ce], default=0),
                          max([e['ntokens'] for e in fe], default=0)))
    print(f'Pages loaded in both where the ping elements differ: {len(diffs)}\n')
    if diffs:
        print('| Page host | Chrome elements | Firefox elements | Chrome max tokens | Firefox max tokens |')
        print('|---|---|---|---|---|')
        for url, a, b, ma, mb in diffs:
            print(f"| {url.split('/')[2]} | {a} | {b} | {ma} | {mb} |")


if __name__ == '__main__':
    main()
