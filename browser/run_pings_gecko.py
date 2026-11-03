# Gecko setups for run_pings.py (Firefox Nightly, headless, with the send_pings prefs).
# Usage: .venv/bin/python -I browser/run_pings_gecko.py SETUP OUT.json
#   SETUP: ff-default | ff-unlimited | ff-sameorigin | ff-off
import os, sys

from selenium import webdriver

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_pings  # noqa: E402

FIREFOX = '/Applications/Firefox Nightly.app/Contents/MacOS/firefox'
PREFS = {
    'ff-default': {'browser.send_pings': True},
    'ff-unlimited': {'browser.send_pings': True, 'browser.send_pings.max_per_link': -1},
    'ff-sameorigin': {'browser.send_pings': True, 'browser.send_pings.max_per_link': -1,
                      'browser.send_pings.require_same_host': True},
    'ff-off': {},
}


def make_driver(setup):
    o = webdriver.FirefoxOptions()
    o.binary_location = FIREFOX
    o.add_argument('-headless')
    for k, v in PREFS[setup].items():
        o.set_preference(k, v)
    return webdriver.Firefox(options=o)


if __name__ == '__main__':
    run_pings.main(make_driver)
