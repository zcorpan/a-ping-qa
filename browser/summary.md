Pings received per click (tokens in the ping attribute → requests logged by the server).

| Case | Tokens | Chrome Canary | Chrome Canary + MathMLAnchorElement | Safari TP | Fx Nightly, defaults | Fx, send_pings | Fx, send_pings, max_per_link=-1 | Fx, send_pings, max_per_link=-1, require_same_host |
|---|---|---|---|---|---|---|---|---|
| `n1` | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| `n2` | 2 | 2 | 2 | 2 | 0 | 1 | 2 | 2 |
| `n3` | 3 | 3 | 3 | 3 | 0 | 1 | 3 | 3 |
| `n4` | 4 | 4 | 4 | 4 | 0 | 1 | 4 | 4 |
| `n5` | 5 | 5 | 5 | 5 | 0 | 1 | 5 | 5 |
| `n8` | 8 | 8 | 8 | 8 | 0 | 1 | 8 | 8 |
| `n10` | 10 | 10 | 10 | 10 | 0 | 1 | 10 | 10 |
| `n16` | 16 | 16 | 16 | 16 | 0 | 1 | 16 | 16 |
| `n32` | 32 | 32 | 32 | 32 | 0 | 1 | 32 | 32 |
| `n64` | 64 | 64 | 64 | 64 | 0 | 1 | 64 | 64 |
| `n100` | 100 | 100 | 100 | 100 | 0 | 1 | 100 | 100 |
| `n128` | 128 | 128 | 128 | 128 | 0 | 1 | 128 | 128 |
| `n256` | 256 | 256 | 256 | 256 | 0 | 1 | 256 | 256 |
| `n257` | 257 | 257 | 257 | 257 | 0 | 1 | 257 | 257 |
| `n500` | 500 | 500 | 356 | 500 | 0 | 1 | 500 | 500 |
| `n1000` | 1000 | 1000 | 351 | 1000 | 0 | 1 | 1000 | 1000 |
| `same_abs` | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| `xport` | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0 |
| `xhost` | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0 |
| `x_then_same` | 2 | 2 | 2 | 2 | 0 | 1 | 2 | 1 |
| `dup` | 2 | 1 | 1 | 2 | 0 | 1 | 2 | 2 |
| `data_first` | 2 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| `js_first` | 2 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| `ftp_first` | 2 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| `invalid_first` | 2 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| `ws_separators` | 4 | 4 | 4 | 4 | 0 | 1 | 3 | 3 |
| `area` | 2 | 2 | 2 | 2 | 0 | 1 | 2 | 2 |
| `svg_a` | 2 | 2 | 2 | 0 | 0 | 1 | 2 | 2 |
| `js_click` | 2 | 2 | 2 | 2 | 0 | 1 | 2 | 2 |
| `blank_target` | 2 | 2 | 2 | 2 | 0 | 1 | 2 | 2 |
| `mathml_a` | 2 | 0 (TimeoutException) | 2 | 2 | 0 | 1 | 2 | 2 |
| `beacon_dispatch` | 3 | 3 | 3 | 3 | 0 | 3 | 3 | 3 |
| `beacon_click` | 3 | 3 | 3 | 3 | 0 | 3 | 3 | 3 |

- Chrome Canary: chrome 159.0.8140.0
- Chrome Canary + MathMLAnchorElement: chrome 159.0.8140.0
- Safari TP: Safari Technology Preview 27.0
- Fx Nightly, defaults: firefox 161.0a1
- Fx, send_pings: firefox 161.0a1
- Fx, send_pings, max_per_link=-1: firefox 161.0a1
- Fx, send_pings, max_per_link=-1, require_same_host: firefox 161.0a1

Repeat runs of the large cases on an idle machine (`*-big-*`), and `slow*` cases where the server holds each ping 0.5 s so the rest queue in flight (`*-slow*`):

| Run | n256 | n257 | n500 | n1000 | slow256 | slow257 | slow300 | slow500 |
|---|---|---|---|---|---|---|---|---|
| `chrome-big-1` | 256/256 | 257/257 | 500/500 | 1000/1000 |  |  |  |  |
| `chrome-big-2` | 256/256 | 257/257 | 500/500 | 1000/1000 |  |  |  |  |
| `chrome-slow` |  |  |  |  | 256/256 | 256/257 | 256/300 | 256/500 |
| `ff-unlimited-big-1` | 256/256 | 257/257 | 500/500 | 1000/1000 |  |  |  |  |
| `ff-unlimited-big-2` | 256/256 | 257/257 | 500/500 | 1000/1000 |  |  |  |  |
| `ff-unlimited-slow-2` |  |  |  |  | 256/256 | 257/257 |  |  |
| `ff-unlimited-slow` |  |  |  |  | 255/256 | 256/257 | 300/300 | 500/500 |
