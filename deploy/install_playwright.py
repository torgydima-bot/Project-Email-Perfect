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

def run(cmd, timeout=180):
    print(f'$ {cmd[:80]}')
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    result = (out + '\n' + err).strip()
    if result:
        print(result[:400])
    print()

run('cd /var/www/email-perfect && venv/bin/pip install playwright', timeout=120)
run('cd /var/www/email-perfect && venv/bin/playwright install chromium --with-deps', timeout=300)
run('cd /var/www/email-perfect && venv/bin/python3 -c "from playwright.sync_api import sync_playwright; print(\'Playwright OK\')"')

client.close()
print('Done!')
