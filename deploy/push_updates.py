import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko
import os

HOST = '77.73.233.5'
USER = 'root'
PASS = 'rUR%3cFj6V%k'
APP_LOCAL = r"c:\Projects Claude Code\Project Email Perfect"
APP_REMOTE = "/var/www/email-perfect"

FILES = [
    "templates/campaigns/preview.html",
    "routes/campaigns.py",
    "services/email_service.py",
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
sftp = client.open_sftp()

for rel in FILES:
    local = os.path.join(APP_LOCAL, rel.replace('/', os.sep))
    remote = APP_REMOTE + '/' + rel
    sftp.put(local, remote)
    print(f'Uploaded: {rel}')

sftp.close()

stdin, stdout, stderr = client.exec_command('systemctl restart email-perfect', timeout=15)
stdout.channel.recv_exit_status()
print('Service restarted')

client.close()
print('Done!')
