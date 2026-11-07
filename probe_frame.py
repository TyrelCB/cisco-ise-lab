from cdp import CDP
import time, json
c = CDP()
# enumerate all frames via DOM
info = c.eval("""(()=>{const f=[...document.querySelectorAll('iframe')];return JSON.stringify(f.map(x=>({src:x.src,w:x.offsetWidth,h:x.offsetHeight,name:x.name,id:x.id})))})()""")
print("frames:", info)
# try to read same-origin iframe body
try:
    body = c.eval("""(()=>{const f=[...document.querySelectorAll('iframe')].find(x=>x.contentDocument);return f?f.contentDocument.body.innerText.slice(0,400):'no accessible frame'})()""")
    print("frame body:", body)
except Exception as e:
    print("frame read err", e)
# also list CDP targets for OOPIFs
import requests
tg = requests.get("http://127.0.0.1:44001/json", timeout=5).json()
for t in tg:
    print("TARGET", t.get("type"), t.get("url","")[:120])
