**Chrome Canary**: 263 of 263 pages loaded; 15 with a non-empty `ping` on `<a>`/`<area>` in some frame; 181 elements.
- Tokens per element: 1: 181
- Ping URL vs frame origin: same origin: 99, cross origin: 82
- Elements by tag and namespace: a (xhtml): 181
- Hidden (no client rects): 1
- `'ping' in HTMLAnchorElement.prototype` in the top frame: True: 263
- Cross-origin ping hosts: `t2965.am-track.pl`: 80, `nr-events.taboola.com`: 2

**Firefox Nightly (send_pings on, max_per_link=-1)**: 263 of 263 pages loaded; 15 with a non-empty `ping` on `<a>`/`<area>` in some frame; 181 elements.
- Tokens per element: 1: 181
- Ping URL vs frame origin: same origin: 99, cross origin: 82
- Elements by tag and namespace: a (xhtml): 181
- Hidden (no client rects): 1
- `'ping' in HTMLAnchorElement.prototype` in the top frame: True: 263
- Cross-origin ping hosts: `t2965.am-track.pl`: 80, `nr-events.taboola.com`: 2

Pages loaded in both where the ping elements differ: 0

