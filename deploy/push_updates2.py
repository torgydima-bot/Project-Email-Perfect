import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko

HOST = '77.73.233.5'
USER = 'root'
PASS = 'rUR%3cFj6V%k'
APP_LOCAL = r"c:\Projects Claude Code\Project Email Perfect"
APP_REMOTE = "/var/www/email-perfect"

FILES = [
    "services/email_service.py",
    "services/ai_service.py",
    "services/email_builder.py",
    "templates/campaigns/builder.html",
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
sftp = client.open_sftp()

import os
for rel in FILES:
    local = os.path.join(APP_LOCAL, rel.replace('/', os.sep))
    remote = APP_REMOTE + '/' + rel
    sftp.put(local, remote)
    print(f'Uploaded: {rel}')

sftp.close()

# Update MANAGER_NAME in .env
def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    result = (out + '\n' + err).strip()
    if result:
        print(result)

run("sed -i 's/MANAGER_NAME=Dmitriy/MANAGER_NAME=Дмитрий/' /var/www/email-perfect/.env")
run("grep MANAGER_NAME /var/www/email-perfect/.env")
run("systemctl restart email-perfect")
print("Service restarted")

client.close()
print('Done!')
