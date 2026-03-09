import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko, os

HOST = '77.73.233.5'
USER = 'root'
PASS = 'rUR%3cFj6V%k'
APP_LOCAL = r"c:\Projects Claude Code\Project Email Perfect"
APP_REMOTE = "/var/www/email-perfect"

FILES = [
    "services/ai_service.py",
    "routes/campaigns.py",
    "templates/campaigns/builder.html",
]

HEADER_LOCAL = r"D:\001 ОРГАНИК\ВК\Фон для рассылки.jpg"
HEADER_REMOTE = "/var/www/email-perfect/static/uploads/header_bg.jpg"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
sftp = client.open_sftp()

for rel in FILES:
    local = os.path.join(APP_LOCAL, rel.replace('/', os.sep))
    remote = APP_REMOTE + '/' + rel
    sftp.put(local, remote)
    print(f'Uploaded: {rel}')

# Upload header image
sftp.put(HEADER_LOCAL, HEADER_REMOTE)
print(f'Uploaded: header_bg.jpg')

sftp.close()

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    result = (out + '\n' + err).strip()
    if result:
        print(result)

# Update HEADER_BG_IMAGE in .env
run("sed -i 's|HEADER_BG_IMAGE=.*|HEADER_BG_IMAGE=http://77.73.233.5:5001/static/uploads/header_bg.jpg|' /var/www/email-perfect/.env")
run("grep HEADER_BG_IMAGE /var/www/email-perfect/.env")
run("systemctl restart email-perfect")
print('Service restarted. Done!')

client.close()
