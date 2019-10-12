import json
import random
import string
import sqlite3

from contextlib import closing

from bottle import run, route, redirect, abort, request, HTTPResponse


class Database:
    def __init__(self, path: str) -> None:
        self.con = sqlite3.connect(path)
        with closing(self.con.cursor()) as cur:
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS urldata
                (identification text, original_url text)
                '''
            )

    def get(self, column_name: str, value: str) -> tuple:
        with closing(self.con.cursor()) as cur:
            cur.execute(
                f'SELECT * FROM urldata WHERE {column_name}=?', (value,))
            data = cur.fetchone()
        return data

    def put(self, identification: str, original_url: str) -> None:
        with closing(self.con.cursor()) as cur:
            cur.execute(
                'INSERT INTO urldata VALUES (?, ?)',
                (identification, original_url)
            )
        self.con.commit()
        return


@route('/<identification>')
def transfer(identification: str) -> None:
    exist = database.get("identification", identification)
    if exist is None:
        return abort(404)
    url = exist[1]
    return HTTPResponse(headers={"Location": url}, status=302)


def generate_response(status: int, data: dict) -> HTTPResponse:
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(data)
    response = HTTPResponse(headers=headers, status=status, body=data)
    return response


def generate_identification() -> str:
    base = string.ascii_letters + string.digits + "_-"
    flag = True
    while flag:
        identification = "".join(random.choices(base, k=10))
        check = database.get("identification", identification)
        if check is not None:
            continue
        flag = False
    return identification


@route("/", method="POST")
def generate_link() -> HTTPResponse:
    if (request.get_header('Content-Type') != "application/json"
            or request.json is None
            or "url" not in request.json):
        response = generate_response(400, {"message": "Bad Request"})
        return response
    url = json.loads(request.json)["url"]
    exist = database.get("original_url", url)
    if exist is None:
        identification = generate_identification()
        database.put(identification, url)
    else:
        identification = exist[0]
    response = generate_response(
        200,
        {
            "message": "Success",
            "shorten_url": f"https://{request.get_header('Host')}/{identification}"
        }
    )
    return response

if __name__ == "__main__":
    database = Database("urlshorter.db")
    run(host='localhost', port=8080)
