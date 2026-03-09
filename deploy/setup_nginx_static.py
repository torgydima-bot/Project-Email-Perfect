import sys, io, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '77.73.233.5'; USER = 'root'; PASS = 'rUR%3cFj6V%k'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    print((out+'\n'+err).strip()[:400]); print()

# Nginx config: only static files on port 8080
nginx_conf = '''server {
    listen 8080;
    server_name _;

    location /static/ {
        alias /var/www/email-perfect/static/;
        expires 30d;
        add_header Access-Control-Allow-Origin *;
    }

    location / {
        return 404;
    }
}'''

run('apt install -y nginx 2>&1 | tail -3', timeout=60)

# Write config
import paramiko
sftp = client.open_sftp()
with sftp.file('/etc/nginx/sites-available/email-static', 'w') as f:
    f.write(nginx_conf)
sftp.close()

run('ln -sf /etc/nginx/sites-available/email-static /etc/nginx/sites-enabled/email-static')
run('rm -f /etc/nginx/sites-enabled/default')
run('nginx -t')
run('systemctl enable nginx && systemctl restart nginx')
run('systemctl status nginx --no-pager | head -5')
run('ufw allow 8080/tcp 2>/dev/null || true')
run('curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/static/uploads/header_bg.jpg')

# Update .env
run("sed -i 's|HEADER_BG_IMAGE=.*|HEADER_BG_IMAGE=http://77.73.233.5:8080/static/uploads/header_bg.jpg|' /var/www/email-perfect/.env")
run("grep HEADER_BG_IMAGE /var/www/email-perfect/.env")

run('systemctl restart email-perfect')
print('Done!')
client.close()
