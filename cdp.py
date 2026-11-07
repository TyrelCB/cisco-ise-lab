#!/usr/bin/env python3
"""Minimal Chrome DevTools Protocol driver for the persistent headed
agent-browser on fedora (CDP :44001). Usage:
  python3 cdp.py eval '<js expression>'      # print JSON result value
  python3 cdp.py navigate <url>
  python3 cdp.py url
"""
import json, sys, requests, websocket

BASE = "http://127.0.0.1:44001"

def page_ws():
    pages = requests.get(BASE + "/json", timeout=5).json()
    page = next(t for t in pages if t.get("type") == "page")
    return page["webSocketDebuggerUrl"]

class CDP:
    def __init__(self):
        self.ws = websocket.create_connection(page_ws(), suppress_origin=True, timeout=30)
        self.id = 0
    def cmd(self, method, **params):
        self.id += 1
        self.ws.send(json.dumps({"id": self.id, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.id:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})
    def eval(self, expr, await_promise=False):
        r = self.cmd("Runtime.evaluate", expression=expr,
                     returnByValue=True, awaitPromise=await_promise)
        exc = r.get("exceptionDetails")
        if exc:
            raise RuntimeError(json.dumps(exc.get("exception", exc))[:400])
        return r.get("result", {}).get("value")
    def navigate(self, url):
        self.cmd("Page.navigate", url=url)

if __name__ == "__main__":
    c = CDP()
    op = sys.argv[1]
    if op == "eval":
        v = c.eval(sys.argv[2], await_promise=(len(sys.argv) > 3 and sys.argv[3] == "await"))
        print(json.dumps(v) if not isinstance(v, str) else v)
    elif op == "navigate":
        c.navigate(sys.argv[2]); print("navigated")
    elif op == "url":
        print(c.eval("location.href"))

# --- same-origin fetch helper (uses the logged-in browser session) ---
_CSRF = None
def api(c, method, path, body=None, ctype="application/json"):
    """Fetch an ISE admin/internal API via the page's own session (httpOnly cookie + CSRF)."""
    global _CSRF
    if _CSRF is None:
        _CSRF = c.eval("""(()=>{const i=[...document.querySelectorAll('input[type=hidden]')].find(x=>(x.value||'').startsWith('OWASP_CSRFTOKEN='));return i?i.value.split('=')[1]:''})()""")
    payload = json.dumps(body) if body is not None else None
    pj = json.dumps(payload)  # JS literal: null or "...json string..."
    js = "(async()=>{const opt={method:%s,headers:{'Accept':'application/json','Content-Type':%s,'OWASP_CSRFTOKEN':%s},credentials:'same-origin'};" \
         "const b=%s;if(b!=null)opt.body=b;" \
         "const r=await fetch(%s,opt);const t=await r.text();" \
         "return JSON.stringify({status:r.status,body:t.slice(0,6000)});})()" % (
        json.dumps(method), json.dumps(ctype), json.dumps(_CSRF), pj, json.dumps(path))
    return json.loads(c.eval(js, await_promise=True))
