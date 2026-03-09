import sys, io, os, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '77.73.233.5'; USER = 'root'; PASS = 'rUR%3cFj6V%k'
APP_LOCAL = r"c:\Projects Claude Code\Project Email Perfect"
APP_REMOTE = "/var/www/email-perfect"

FILES = [
    "services/email_service.py",
    "services/scraper.py",
    "routes/campaigns.py",
    "templates/campaigns/builder.html",
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
sftp = client.open_sftp()
for rel in FILES:
    sftp.put(os.path.join(APP_LOCAL, rel.replace('/', os.sep)), APP_REMOTE + '/' + rel)
    print(f'OK: {rel}')
sftp.close()

stdin, stdout, stderr = client.exec_command('systemctl restart email-perfect', timeout=15)
stdout.channel.recv_exit_status()
print('Restarted')
client.close()
