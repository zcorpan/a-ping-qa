# Table of pings received per case and setup from browser/results/*.json.
# Usage: python3 -I browser/summarize.py > browser/summary.md
import json, os

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
SETUPS = [('chrome', 'Chrome Canary'), ('chrome-mathml', 'Chrome Canary + MathMLAnchorElement'),
          ('safari-tp', 'Safari TP'), ('ff-off', 'Fx Nightly, defaults'),
          ('ff-default', 'Fx, send_pings'), ('ff-unlimited', 'Fx, send_pings, max_per_link=-1'),
          ('ff-sameorigin', 'Fx, send_pings, max_per_link=-1, require_same_host')]


def load(name):
    p = os.path.join(DIR, name + '.json')
    if not os.path.exists(p):
        return None
    r = json.load(open(p))
    cases = {c['case']: c for c in r['cases']}
    extra = os.path.join(DIR, name + '-extra.json')
    if os.path.exists(extra):  # later rerun of some cases; it wins
        e = json.load(open(extra))
        cases |= {c['case']: c for c in e['cases']}
    return r, cases


def main():
    data = [(label, load(name)) for name, label in SETUPS]
    data = [(label, d) for label, d in data if d]
    print('Pings received per click (tokens in the ping attribute → requests logged by the server).\n')
    print('| Case | Tokens | ' + ' | '.join(label for label, _ in data) + ' |')
    print('|---|---|' + '---|' * len(data))
    order = list(data[0][1][1].keys())
    for label, (_, cases) in data[1:]:
        order += [c for c in cases if c not in order]
    for cid in order:
        tokens = next(d[1][cid]['tokens'] for _, d in data if cid in d[1])
        cells = []
        for _, (_, cases) in data:
            c = cases.get(cid)
            cells.append('' if c is None else f"{c['received']}" + (f" ({c['error']})" if c.get('error') else ''))
        print(f'| `{cid}` | {tokens} | ' + ' | '.join(cells) + ' |')
    print()
    for label, (r, _) in data:
        print(f"- {label}: {r['browser']} {r['version']}")


if __name__ == '__main__':
    main()
