# Gecko variant of live_dom.py: Firefox Nightly headless with browser.send_pings on.
# Usage: .venv/bin/python -I live_dom_gecko.py firefox data/live-pages.jsonl OUT.jsonl [WORKERS]  (appends; skips pages already done)
import os, sys

from selenium import webdriver

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import live_dom  # noqa: E402

FIREFOX = '/Applications/Firefox Nightly.app/Contents/MacOS/firefox'


def make_driver_firefox():
    o = webdriver.FirefoxOptions()
    o.binary_location = FIREFOX
    o.add_argument('-headless')
    o.add_argument('--width=1366')
    o.add_argument('--height=900')
    o.set_preference('browser.send_pings', True)
    o.set_preference('browser.send_pings.max_per_link', -1)
    o.page_load_strategy = 'eager'
    return webdriver.Firefox(options=o)


if __name__ == '__main__':
    live_dom.run(make_driver_firefox, sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 2)
