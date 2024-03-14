import sqlite3

from urllib.parse import urlparse, parse_qs

def _normalize_path(path):
    parsed_url = urlparse(path)
    q = parse_qs(parsed_url.query)

    res = parsed_url.path
    params_keys = sorted(q.keys())
    for k in params_keys:
        if k == "draw":
            # dirty trick for a website
            continue
        v = "".join(q[k]).lower()
        res += "#" + k + "=" + v
    return res

def _normalize_body(body):
    return body \
        .replace(" ",  "") \
        .replace("\t", "") \
        .replace("\n", "")

class RequestDatabase(object):
    def __init__(self, filename):
        self.filename = filename
        self.conn     = sqlite3.connect(filename)
        if self.conn is None:
            raise ValueError("unable to open the database")

        sql_req_table = \
            "CREATE TABLE IF NOT EXISTS requests (\n" + \
            "  hostname     text    KEY,\n" + \
            "  method       text    KEY,\n" + \
            "  path         text    KEY,\n" + \
            "  body         text    KEY,\n" + \
            "  resp_status  integer NOT NULL,\n" + \
            "  resp_headers text    NOT NULL,\n" + \
            "  resp_body    blob\n" + \
            ");"
        self.conn.execute(sql_req_table)

    def add_request(self, hostname: str, method: str, path: str, body: str,
                    resp_status: int, resp_headers: str, resp_body: bytes):
        body = _normalize_body(body)
        path = _normalize_path(path)

        if self.get_request(hostname, method, path, body) != None:
            return
            # self.delete_request(method, path, body)

        sql_insert_request = \
            "INSERT INTO requests\n" + \
            "  (hostname, method, path, body, resp_status, resp_headers, resp_body) VALUES (?, ?, ?, ?, ?, ?, ?);"
        cursor = self.conn.cursor()
        cursor.execute(sql_insert_request, (hostname, method, path, body, resp_status, resp_headers, resp_body))
        self.conn.commit()
        cursor.close()

    def delete_request(self, hostname: str, method: str, path: str, body: str):
        body = _normalize_body(body)
        path = _normalize_path(path)

        sql_delete_req = \
            "DELETE FROM requests WHERE " + \
                "hostname=? AND method=? AND path=? AND body=?;"
        cursor = self.conn.cursor()
        cursor.execute(sql_delete_req, (hostname, method, path, body))

    def get_request(self, hostname: str, method: str, path: str, body: str) -> tuple:
        body = _normalize_body(body)
        path = _normalize_path(path)

        sql_get_request = \
            "SELECT resp_status, resp_headers, resp_body FROM requests WHERE\n" + \
                "hostname=? AND method=? AND path=? AND body=?;"

        cursor = self.conn.cursor()
        cursor.execute(sql_get_request, (hostname, method, path, body))

        rows = cursor.fetchall()
        if len(rows) == 0:
            return None

        if len(rows) != 1:
            print(f"!Err: multiple rows for ({hostname}, {method}, {path}, {body})")
        return rows[0]
