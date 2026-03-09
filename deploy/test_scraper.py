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

cmd = '''cd /var/www/email-perfect && venv/bin/python3 -c "
from services.scraper import fetch_product_text
result = fetch_product_text('https://perfect-org.ru/asconodum')
print('LENGTH:', len(result))
print('FIRST 500:', result[:500])
"'''

stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace').strip()
err = stderr.read().decode('utf-8', errors='replace').strip()
print(out)
if err:
    print('ERR:', err[:300])

client.close()
