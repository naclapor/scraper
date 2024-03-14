#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from mitmproxy import http, proxy
from reqdb import RequestDatabase

import threading
import logging
import json
import os

conn           = None
httpServerPort = 8081

class S(BaseHTTPRequestHandler):
    def _set_response(self, code: int, headers: str, body: bytes):
        self.send_response(code)
        headers_json = json.loads(headers)
        for k in headers_json:
            v = headers_json[k]
            if v == "":
                continue
            if k.lower() == "content-length":
                continue
            self.send_header(k, v)
        if len(body) > 0:
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        written = 0
        while written < len(body):
            written += self.wfile.write(body[written:])
        self.wfile.flush()

    def _set_no_content_response(self):
        self.send_response(404)
        body = b"<html><h1>content not in cache</h1></html>"
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        written = 0
        while written < len(body):
            written += self.wfile.write(body[written:])
        self.wfile.flush()

    def _set_internal_error_response(self, err: str):
        self.send_response(500)
        body = b"<html><h1>internal error: %s</h1></html>" % err.encode(errors="ignore")
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        written = 0
        while written < len(body):
            written += self.wfile.write(body[written:])
        self.wfile.flush()

    def _handle_request(self, method: str):
        if "original-host" not in self.headers:
            self._set_internal_error_response("original-host not set, you are not using the replayer proxy")
            return

        if "Content-Length" in self.headers:
            content_length = int(self.headers["Content-Length"])
            client_data = self.rfile.read(content_length)
        else:
            client_data = b""

        hostname = self.headers["original-host"]
        method   = method
        path     = self.path
        body     = client_data.decode("utf-8", errors="ignore")

        t = conn.get_request(hostname, method, path, body)
        if t is None:
            self._set_no_content_response()
            return

        resp_status, resp_headers, resp_body = t
        if resp_body is None:
            resp_body = b""

        self._set_response(resp_status, resp_headers, resp_body)

    do_GET     = lambda self: self._handle_request("GET")
    do_POST    = lambda self: self._handle_request("POST")
    do_HEAD    = lambda self: self._handle_request("HEAD")
    do_PUT     = lambda self: self._handle_request("PUT")
    do_OPTIONS = lambda self: self._handle_request("OPTIONS")
    do_DELETE  = lambda self: self._handle_request("DELETE")

    def log_message(self, format, *args):
        # shut the fuck up...
        return

def _runHttpServer(server_class=HTTPServer, handler_class=S, port=httpServerPort):
    global conn
    if not "SCRAPER_TARGET_NAME" in os.environ or not os.environ["SCRAPER_TARGET_NAME"]:
        print("!Err: \"SCRAPER_TARGET_NAME\" env variable not set")
        exit(1)

    target_name = os.environ["SCRAPER_TARGET_NAME"]
    dbfile = os.path.join(
        os.path.realpath(os.path.dirname(__file__)),
        "dbs",
        f"{target_name}.db")

    try:
        conn = RequestDatabase(dbfile)
    except ValueError:
        print("!Err: unable to load database")
        exit(1)

    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd on localhost:%d', port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd')

## Mitmproxy Handlers
def request(flow: http.HTTPFlow) -> None:
    flow.request.headers["original-host"] = flow.request.pretty_host
    flow.request.headers["Host"]          = "localhost"
    flow.request.authority = "localhost"
    flow.request.host      = "localhost"
    flow.request.port      = httpServerPort
    flow.request.scheme    = "http"

def server_connect(data: proxy.server_hooks.ServerConnectionHookData):
    host, _ = data.server.address
    if host != "localhost":
        # we do not want to connect to other servers than ourselves
        # indeed, all connections are forwarded to localhost
        data.server.tls     = False
        data.server.address = "localhost", httpServerPort

## Main Script
t = threading.Thread(target=_runHttpServer)
t.start()
