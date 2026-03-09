import sys, io, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '77.73.233.5'; USER = 'root'; PASS = 'rUR%3cFj6V%k'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    print((out+'\n'+err).strip()); print()

run('systemctl is-active nginx && echo NGINX_RUNNING || echo NGINX_NOT_RUNNING')
run('curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/static/uploads/header_bg.jpg')
run('ls -la /var/www/email-perfect/static/uploads/header_bg.jpg')

client.close()
