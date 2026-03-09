import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import paramiko

HOST = '77.73.233.5'
USER = 'root'
PASS = 'rUR%3cFj6V%k'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)
sftp = client.open_sftp()
sftp.put(r"c:\Projects Claude Code\Project Email Perfect\services\scraper.py",
         "/var/www/email-perfect/services/scraper.py")
sftp.close()
print("Uploaded scraper.py")

cmd = r'''cd /var/www/email-perfect && venv/bin/python3 -c "
from services.scraper import fetch_product_text
result = fetch_product_text('https://perfect-org.ru/asconodum')
print('LENGTH:', len(result))
print('FIRST 600:')
print(result[:600])
"'''

stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace').strip()
err = stderr.read().decode('utf-8', errors='replace').strip()
print(out[:2000])
if err:
    print('ERR:', err[:300])

stdin, stdout, stderr = client.exec_command('systemctl restart email-perfect', timeout=15)
stdout.channel.recv_exit_status()
print('Service restarted')

client.close()
print('Done!')
