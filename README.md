# `<a ping>` web compat: how pages use it, and how many ping URLs browsers send

For [bug 2088500](https://bugzilla.mozilla.org/show_bug.cgi?id=2088500) (`browser.send_pings.max_per_link`) and [bug 951104](https://bugzilla.mozilla.org/show_bug.cgi?id=951104) (enable `<a ping>`).

Gecko implements hyperlink auditing behind `browser.send_pings` (off by default), with
`browser.send_pings.max_per_link` (default 1) and `browser.send_pings.require_same_host`
(default false). This measures what Firefox Nightly, Chrome Canary and Safari TP send per click,
and how pages use `ping` in markup and scripts, to see how many ping URLs per link are needed
for web compat.

## Scope

- Corpora: the 12 local Common Crawl CC-MAIN-2026-39 WARCs (seed 11397, all crawled URLs) and
  HTTP Archive's `sample_data.requests_10k` (2026-10-01, desktop and mobile). A 1% `TABLESAMPLE`
  of `crawl.requests` wasn't used: its dry run reports the whole `response_body` column, and
  `--maximum_bytes_billed` is checked against that estimate, even though a sampled query
  bills less.
- BigQuery budget: 0.5 TiB for the run.
- Browsers: Firefox Nightly and Chrome Canary headless; Safari TP (no headless mode) only for the
  local test page.
- Live pages: final DOM only (no clicks, so no real pings sent). The Chrome use counter
  (`HTMLAnchorElementPingAttribute`) fires on click, which the crawl doesn't do, so it isn't used.

## Summary

- Every `ping` attribute found has exactly one URL: 118 `<a>`/`<area>` elements on 13 pages in
  Common Crawl (255,716 HTML responses), 203 elements on 12 pages in the HTTP Archive 10k sample,
  and every script pattern found sets a single URL. The one script that can build a longer list
  is Awin's (`www.dwin2.com`): it appends its beacon URL to an existing `ping` value, and sends the
  same data with `navigator.sendBeacon` too.
- Loading the 263 pages that use `ping` (or load a script that does) in Chrome Canary and
  Firefox Nightly gives the same final DOM in both: 181 `<a ping>` on 15 pages, all 1 URL.
- So a cap of 1 URL per link (Gecko's `max_per_link` default) covers every use seen; nothing in
  either corpus needs more. No page behavior depends on the pings being sent (they're
  fire-and-forget), so what's lost to a cap or to pings being off is the site's click tracking.
- Chrome Canary and Safari TP send every http(s) token (1000 of 1000); Chrome is capped only
  by the network service's limit of 256 in-flight keepalive requests per top-level frame (see
  `browser/summary.md` for the slow-server cases). Firefox Nightly with `browser.send_pings` sends
  the first 1; with `max_per_link=-1`, all.
- Cross-origin ping URLs are common: `require_same_host` (which is a same-origin check, a
  different port is blocked too) would drop Taboola's and other third-party trackers' pings
  (81 of 118 Common Crawl tokens, 2 of 203 HTTP Archive tokens; Google Search's are same-origin).
- The most common script use is an ad beacon in AdPushup-derived libraries (Geniee, AdPushup,
  AdRecover; 110 desktop and 99 mobile pages in the 10k sample): a hidden
  `<a href="javascript:void(0)">` whose `ping` is set before each synthetic `click`. It's only
  the fallback when `navigator.sendBeacon` is missing, and all three browsers send those pings
  (one per synthetic click).
- `'ping' in HTMLAnchorElement.prototype` is true in Firefox with pings off, so feature detection
  (Modernizr's, AdPushup's) already assumes pings work in Firefox.

Other differences found on the test page (spec: [hyperlink auditing](https://html.spec.whatwg.org/multipage/links.html#hyperlink-auditing)):

- Firefox splits on space, tab, LF and CR but not form feed (`nsWhitespaceTokenizer`), unlike
  the spec's ASCII whitespace; Chrome and Safari split on form feed ([bug 2088508](https://bugzilla.mozilla.org/show_bug.cgi?id=2088508)).
- Firefox sends a `Referer` header with cross-origin pings from `http:` pages; the spec says
  referrer `no-referrer` (since whatwg/html#712), and Chrome and Safari send none
  ([bug 2088505](https://bugzilla.mozilla.org/show_bug.cgi?id=2088505)).
- Chrome collapses duplicate URLs into one ping (`SpaceSplitString` dedupes); Firefox and Safari
  send both.
- Safari TP sends no pings for SVG `<a ping>` (WebKit's `SVGAElement` doesn't call
  `sendPings`); Chrome and Firefox do.
- MathML `<a ping>`: Firefox Nightly (`mathml.a.element.enabled`, on in Nightly) and Safari TP
  send pings; Chrome Canary doesn't by default (no `MathMLAnchorElement`: not a link), and does
  with `--enable-blink-features=MathMLAnchorElement`.
- In Gecko, a URL that fails to open still counts toward `max_per_link` (`nsPingListener.cpp`),
  so with `require_same_host` on and the default cap, a cross-origin first URL means no ping at
  all (from source, not tested).

## 1. Corpora

### Common Crawl

`cc_scan.py` over the 12 WARCs (`data/cc-totals.json`: 255,716 HTTP 200 HTML responses up to
3 MB). Its prefilter (`ping\s*=` or a quoted `"ping"`) matches every element with a non-empty
`ping` attribute, so markup recall is complete for those bodies; candidates are parsed with lexbor
(selectolax), and inline scripts are searched for `setAttribute("ping"`, `.attr("ping"`,
`"ping" in`, `.ping =`, and `<a … ping=` strings. Output: `data/cc-hits.jsonl` (43 pages).

- 13 pages have `<a>`/`<area>` with a non-empty `ping`: 118 elements, all with 1 token; 37 tokens
  same host, 81 cross host (one Polish site's links to its tracking host, and Taboola).
- Several are Google Search result links pasted into pages, with a relative `/url?…` ping that
  resolves against the site that pasted them.
- Inline scripts: a search-results template with `ping="%ping%"`, and a component copying
  `data-ping` to `ping`; the rest of the `.ping =` hits are unrelated objects.

### HTTP Archive

`queries/ping_10k.sql` scans `httparchive.sample_data.requests_10k` (2026-10-01) for the same
patterns in any response body (0.152 TiB). The result was slimmed with
`queries/ping_10k_slim.sql` (keeps bodies only for HTML with a `ping` attribute; 0.005 TiB) and
downloaded (not committed: `crawl/`). `ha_classify.py` parses the HTML and groups script snippets
by script URL and pattern; `build_live_list.py`'s `script_kind()` decides which script hits set
`ping` on links; `ha_summary.py` gives `data/ha-summary.md`. Denominators from
`queries/pages_10k_counts.sql`.

| | desktop | mobile |
|---|---|---|
| Pages in sample (root) | 11217 (6013) | 13363 (7244) |
| `<a ping>`/`<area ping>` in crawled HTML (root) | 5 (5) | 7 (7) |
| Script: AdPushup-derived ad beacon (Geniee, AdPushup, AdRecover) | 110 (110) | 99 (99) |
| Script: Taboola Newsroom | 31 (31) | 30 (30) |
| Script: Google Search | 2 (2) | 4 (4) |
| Script: HubSpot login/signup UI | 4 (4) | 1 (1) |
| Script: Awin (dwin2) | 1 (1) | 0 (0) |
| Script: other (one site each) | 15 (15) | 16 (16) |

Elements in crawled HTML: 203, all with 1 token; 201 same host (Google Search, a Japanese
ranking site pinging its own `/cc/` URLs, one pasted Google link), 2 cross host
(Taboola).

What the scripts do (read from crawled snippets and, for AdRecover and Awin, live copies of the
scripts):

- AdPushup-derived ad beacon: picks `sendBeacon` when available; otherwise, on Chrome, Safari or
  Opera with `ping` supported, it fires each beacon as a synthetic click on a hidden
  `javascript:` link with `ping` set to one URL (read in AdRecover's live copy; Geniee's crawled
  snippets have the same structure).
- Taboola Newsroom: sets one cross-origin `nr-events.taboola.com` URL on its links.
- Google Search: result links carry one same-origin `/url?…` ping; scripts copy or extend that
  one URL string.
- Awin bounceless tracking: on `mousedown` on an affiliate link, sends a beacon with
  `sendBeacon`, then appends a `zenaps.com` beacon URL to the link's `ping` (keeping existing
  tokens), so a link that already had a ping ends up with 2.
- One site each: HubSpot's login UI, Microsoft Store web components, Yahoo! JAPAN search (sets
  `ping` on click), and a few others, all with one URL.

## 2. Browsers on a local test page

`browser/ping_server.py` serves a test page on two ports and logs each ping request.
`browser/run_pings.py` (Chrome, Safari) and `browser/run_pings_gecko.py` (Firefox prefs) add a
link per case, click it with WebDriver (or `click()`/a synthetic `click` event), and count the
requests that arrive. Results in `browser/results/`, table in `browser/summary.md`.

Browsers: Chrome Canary 159.0.8140.0, Safari TP 255 (WebDriver reports 27.0), Firefox Nightly
161.0a1. Firefox setups: defaults (pings off), `browser.send_pings`, plus
`max_per_link=-1`, plus `require_same_host`.

| Case | Chrome Canary | Safari TP | Fx, send_pings | Fx, send_pings, max_per_link=-1 |
|---|---|---|---|---|
| 1 to 257 same-origin tokens | all | all | 1 | all |
| 500, 1000 tokens, fast local server | all in 3 runs; 356 and 351 in 1 | all | 1 | all |
| 257 to 500 tokens, server holds each ping 0.5 s | 256 | not run | 1 | all |
| cross-origin first, then same-origin | 2 | 2 | 1 (the first) | 2 |
| same URL twice | 1 | 2 | 1 | 2 |
| `data:`/`javascript:`/`ftp:`/invalid first, then http | 1 | 1 | 1 (the http one) | 1 |
| tokens separated by LF, tab, FF (4) | 4 | 4 | 1 | 3 |
| `<area>`, `click()` | all | all | 1 | all |
| SVG `<a>` | all | 0 | 1 | all |
| MathML `<a>` | 0 (2 with `MathMLAnchorElement`) | 2 | 1 | 2 |
| hidden `javascript:` link, `ping` set before each of 3 synthetic clicks | 3 | 3 | 3 | 3 |

With pings off (Firefox defaults) nothing is sent. `require_same_host` blocks pings to another
port as well as another host (it's a same-origin check), and with `max_per_link=-1` the
same-origin token after a blocked one is still sent. Chrome's 256 is the network service's
in-flight keepalive cap per top-level frame (`kMaxKeepaliveConnectionsPerTopLevelFrame` in
`services/network/url_loader_factory.cc`): requests past it fail with
`ERR_INSUFFICIENT_RESOURCES`, so how many get through depends on how fast the ping server
answers. The cap is shared with `fetch(…, {keepalive: true})` and `sendBeacon` from the same
frame.

## 3. Live pages

`build_live_list.py` lists 263 pages (`data/live-pages.jsonl`): HTTP Archive pages with ping
markup or a matching script, and Common Crawl pages with ping markup or the inline template.
`live_dom.py` (Chrome Canary) and `live_dom_gecko.py` (Firefox Nightly, `send_pings` on,
`max_per_link=-1`) load each page headless at 1366×900, wait 8 s, and record every element with
a `ping` attribute in every frame (WebDriver switches into cross-origin frames too): tag,
namespace, token count, ping hosts and whether each is same-origin. No clicks, and full URLs
aren't kept (`out/live-*.jsonl`, summary in `data/live-summary.md`).

- Both browsers: 263 pages loaded, 15 with `<a ping>` in some frame, 181 elements, all with
  1 token; 99 same-origin, 82 cross-origin (80 to one Polish site's tracking host, 2 to
  Taboola). No page differed between the browsers.
- `'ping' in HTMLAnchorElement.prototype` was true on every page in both, including Firefox.
- The ad-beacon libraries' hidden link wasn't in any final DOM, as expected: both browsers
  have `sendBeacon`. Taboola's script was on 43 of the pages but its ping on only 2 live; I think
  it sets `ping` on click.

`live_dom.py` was fixed mid-run (it started a new driver per page); the output from before the
fix was discarded, and both committed runs are from the fixed version.

## Not covered

- Clicks on live pages: pings set at click time (Awin, Yahoo! JAPAN) aren't in the final DOM,
  and no real pings were sent. Google Search showed a consent or bot page live, so its usage is
  from the crawl only.
- Pages behind logins, and deep pages the crawls don't reach.
- Safari TP's behavior with many slow pings (not run, to keep its window short).

## Query bytes

All on the 2026-10-01 10k sample, run on 2026-11-03:

| Query | Bytes processed |
|---|---|
| `queries/ping_10k.sql` | 167,348,535,296 |
| `queries/ping_10k_slim.sql` | 4,963,958,784 |
| `queries/pages_10k_counts.sql` | about 200 KB (10 MB minimum billed) |

## Reproduce

```sh
python3 -m venv .venv && .venv/bin/pip install warcio selectolax selenium
.venv/bin/python -I cc_scan.py data ~/git/commoncrawl/cc-data/CC-MAIN-2026-39/*.warc.gz
bq query --use_legacy_sql=false --max_rows=0 < queries/ping_10k.sql   # then ping_10k_slim.sql on its result table
python3 -I bq_download.py <result table> crawl/ha-10k.jsonl
.venv/bin/python -I ha_classify.py crawl/ha-10k.jsonl data
python3 -I build_live_list.py crawl/ha-10k.jsonl data/ha-elements.jsonl data/cc-hits.jsonl data/live-pages.jsonl
.venv/bin/python -I ha_summary.py crawl/ha-10k.jsonl queries/pages_10k_counts.csv > data/ha-summary.md
python3 -I browser/ping_server.py 18431 18432 &
.venv/bin/python -I browser/run_pings.py chrome browser/results/chrome.json
.venv/bin/python -I browser/run_pings_gecko.py ff-default browser/results/ff-default.json
python3 -I browser/summarize.py > browser/summary.md
.venv/bin/python -I live_dom.py chrome data/live-pages.jsonl out/live-chrome.jsonl 4
.venv/bin/python -I live_dom_gecko.py firefox data/live-pages.jsonl out/live-firefox.jsonl 4
```

Live pages change, so a rerun won't match exactly.
