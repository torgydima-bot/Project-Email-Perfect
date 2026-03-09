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

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    result = (out + '\n' + err).strip()
    if result:
        print(result)
    print()

# Список продуктов с URL
run('cd /var/www/email-perfect && venv/bin/python3 -c "from app import create_app; from db.models import db, Product; app=create_app(); ctx=app.app_context(); ctx.push(); products=Product.query.all(); [print(f\'{p.id}: {p.name[:30]!r} | url={p.url!r} | photo={p.photo_filename!r}\') for p in products]"')

# Список файлов в uploads
run('ls /var/www/email-perfect/static/uploads/ 2>/dev/null | head -20 || echo "empty"')

client.close()
