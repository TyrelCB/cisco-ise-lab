from cdp import CDP
import time, base64
c = CDP()
shot = c.cmd('Page.captureScreenshot', format='png')
open('shot.png','wb').write(base64.b64decode(shot['data']))
print('saved')
