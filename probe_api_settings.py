from cdp import CDP
import time
c = CDP()
c.eval("location.href='https://10.10.20.77/admin/#administration/administration_system/administration_system_settings'")
time.sleep(7)
c.eval("""(()=>{[...document.querySelectorAll('div')].forEach(d=>{if(/Improve your endpoint profiling/.test(d.textContent)&&d.querySelector('button')&&d.getBoundingClientRect().width>400)d.remove()});return 1})()""")
info = c.eval("""(()=>{const el=[...document.querySelectorAll('a,span,div')].filter(x=>(x.textContent||'').trim()==='API Settings'&&x.children.length===0).map(x=>{const r=x.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}});return el[0]||null})()""")
print("nav pos", info)
for t in ['mousePressed','mouseReleased']:
    c.cmd('Input.dispatchMouseEvent', type=t, x=info['x'], y=info['y'], button='left', clickCount=1)
time.sleep(5)
t = c.eval("document.body.innerText")
i = t.find('API Services')
if i < 0:
    i = t.find('ERS')
print("---- page text around API ----")
print(t[i:i+1500] if i >= 0 else t[-1500:])
