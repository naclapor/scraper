import json
import os

from reqdb import RequestDatabase
from mitmproxy import http

db = None

def process_headers(headers):
    res = {}
    for k in headers:
        kl = k.lower()
        if kl == "content-type":
            res[k] = headers[k]
        elif kl == "location":
            res[k] = headers[k]
    return json.dumps(res)

## Mitmproxy Handler
def response(flow: http.HTTPFlow) -> None:
    if not flow.response:
        return
    if not flow.response.headers:
        return

    hostname     = flow.request.pretty_host
    method       = flow.request.method
    path         = flow.request.path
    body         = ""
    resp_status  = flow.response.status_code
    resp_data    = None
    resp_headers = process_headers(flow.response.headers)

    if flow.request.content:
        body = flow.request.content.decode("utf-8", errors="ignore")
    if flow.response.content:
        resp_data = flow.response.content

    db.add_request(hostname, method, path, body, resp_status, resp_headers, resp_data)

## Main Script
if not "SCRAPER_TARGET_NAME" in os.environ or not os.environ["SCRAPER_TARGET_NAME"]:
    print("!Err: \"SCRAPER_TARGET_NAME\" env variable not set")
    exit(1)

target_name = os.environ["SCRAPER_TARGET_NAME"]
dbfile = os.path.join(
    os.path.realpath(os.path.dirname(__file__)),
    "dbs",
    f"{target_name}.db")

try:
    db = RequestDatabase(dbfile)
except ValueError:
    print("!Err: unable to open the database")
    exit(1)
