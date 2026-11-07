#!/usr/bin/env python3
"""ISE ERS automation demo — DevNet on-demand ISE sandbox (ise-sandbox).

Proves a full create -> verify -> cleanup lifecycle over the External RESTful
Services (ERS) API with nothing but `requests`:

  1. login check            GET  /ers/config/internaluser (inventory count)
  2. create identity group  POST /ers/config/identitygroup
  3. create internal user   POST /ers/config/internaluser
  4. attach user -> group   GET/PUT identitygroup (member reference)
  5. verify by search       GET  /ers/config/internaluser/search/{name}
  6. cleanup                DELETE user, DELETE group

Run:  python3 ise_automation_demo.py [--host 10.10.20.77]

Notes learned from this sandbox:
  * ERS is served on 443 (not the classic 9060/9061/9062).
  * The ERS version header is mandatory (this script uses ERS: 4).
  * TLS is a self-signed lab cert -> verify=False.
"""
import argparse, json, sys, time
import requests, urllib3
urllib3.disable_warnings()

HEADERS = {"Accept": "application/json", "Content-Type": "application/json", "ERS": "4"}


class ISE:
    def __init__(self, host, user, pw):
        self.base = f"https://{host}"
        self.s = requests.Session(auth=(user, pw), verify=False, headers=HEADERS)

    def req(self, method, path, **kw):
        r = self.s.request(method, self.base + path, timeout=30, **kw)
        return r

    def jget(self, path):
        r = self.req("GET", path)
        return r.status_code, (r.json() if r.text else None)

    def post(self, path, body):
        r = self.req("POST", path, data=json.dumps(body))
        loc = r.headers.get("Location", "")
        return r.status_code, loc

    def put(self, path, body):
        return self.req("PUT", path, data=json.dumps(body)).status_code

    def delete(self, path):
        return self.req("DELETE", path).status_code


def step(n, msg, ok=True, extra=""):
    print(f"[{'OK' if ok else 'FAIL'}] step {n}: {msg} {extra}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="10.10.20.77")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--password", default="QAWSedrf1234!")
    args = ap.parse_args()
    ise = ISE(args.host, args.user, args.password)
    stamp = time.strftime("%m%d%H%M%S")
    grp_name, usr_name = f"LB-Demo-Grp-{stamp}", f"lb-demo-user-{stamp}"
    grp_id = usr_id = None
    rc = 0

    # 1. inventory count (login + read path)
    code, j = ise.jget("/ers/config/internaluser?size=1")
    total = j["SearchResult"]["total"] if j else "?"
    rc |= not step(1, f"ERS login+read OK, internal users={total}", code == 200)

    # 2. create identity group
    code, loc = ise.post("/ers/config/identitygroup", {
        "CustomIdentityGroup": {"name": grp_name, "description": "created by ise_automation_demo.py",
                                "idStoreName": "Internal Endpoints", "groupId": ["-72"]}})
    grp_id = loc.rsplit("/", 1)[-1] if loc else None
    rc |= not step(2, f"create group {grp_name}", code == 201, f"id={grp_id}")

    # 3. create internal user
    code, loc = ise.post("/ers/config/internaluser", {
        "InternalUser": {"name": usr_name, "userName": usr_name,
                         "userStatus": "Enabled", "enablePasswordAuth": True,
                         "password": "Lb!Demo2026"}})
    usr_id = loc.rsplit("/", 1)[-1] if loc else None
    rc |= not step(3, f"create user {usr_name}", code == 201, f"id={usr_id}")

    # 4. attach user to group via group PUT (custom identity members)
    code, gj = ise.jget(f"/ers/config/identitygroup/{grp_id}")
    g = gj["CustomIdentityGroup"]
    g["customIdentityUsers"] = [{"id": usr_id, "name": usr_name}]
    code = ise.put(f"/ers/config/identitygroup/{grp_id}", gj)
    rc |= not step(4, "attach user -> group", code == 200)

    # 5. verify user via search endpoint
    code, j = ise.jget(f"/ers/config/internaluser/search/name/{usr_name}")
    found = j and j["SearchResult"]["total"] == 1
    rc |= not step(5, "search verifies user", found)

    # 6. cleanup
    c1 = ise.delete(f"/ers/config/internaluser/{usr_id}") if usr_id else 0
    c2 = ise.delete(f"/ers/config/identitygroup/{grp_id}") if grp_id else 0
    rc |= not step(6, f"cleanup user={c1} group={c2}", c1 == 204 and c2 == 204)

    print("RESULT:", "ALL PASS" if rc == 0 else "FAILURES — see above")
    sys.exit(rc)


if __name__ == "__main__":
    main()
