from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import os
os.makedirs('/home/tyrel/projects/cisco-ise-lab/backups', exist_ok=True)
auth = DummyAuthorizer()
auth.add_user('isebackup', 'Backup123!', '/home/tyrel/projects/cisco-ise-lab/backups', perm='elradfmw')
h = FTPHandler
h.authorizer = auth
FTPServer(('0.0.0.0', 21), h).serve_forever()
