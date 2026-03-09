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
    print(f'$ {cmd}')
    result = (out + '\n' + err).strip()
    if result:
        print(result)
    print()
    return result

run('cd /var/www/email-perfect && venv/bin/python3 -c "from app import create_app; from db.models import db, Contact; app=create_app(); ctx=app.app_context(); ctx.push(); contacts=Contact.query.order_by(Contact.id.desc()).limit(10).all(); [print(f\'{c.id}: {c.email} | {c.first_name} {c.last_name} | source={c.source} | {c.created_at}\') for c in contacts]"')

client.close()
