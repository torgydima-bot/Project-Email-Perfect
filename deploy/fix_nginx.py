import sys, io, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '77.73.233.5'; USER = 'root'; PASS = 'rUR%3cFj6V%k'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    result = (out + '\n' + err).strip()[:500]
    if result: print(result)
    print()

nginx_conf = 'server {\n    listen 8080;\n    server_name _;\n\n    location /ep-static/ {\n        alias /var/www/email-perfect/static/;\n        expires 30d;\n        add_header Access-Control-Allow-Origin *;\n    }\n\n    location /static/ {\n        alias /var/www/email-perfect/static/;\n        expires 30d;\n        add_header Access-Control-Allow-Origin *;\n    }\n\n    location / {\n        return 404;\n    }\n}\n'

sftp = client.open_sftp()
with sftp.file('/etc/nginx/sites-available/email-static', 'w') as f:
    f.write(nginx_conf)
sftp.close()

run('nginx -t')
run('systemctl start nginx')
run('systemctl status nginx --no-pager | head -5')
run('curl -s -o /dev/null -w "ep-static: %{http_code}" http://localhost:8080/ep-static/uploads/header_bg.jpg')
run("sed -i 's|HEADER_BG_IMAGE=.*|HEADER_BG_IMAGE=https://sniquatoozoosid.beget.app/ep-static/uploads/header_bg.jpg|' /var/www/email-perfect/.env")
run("grep HEADER_BG_IMAGE /var/www/email-perfect/.env")
run('systemctl restart email-perfect')
print('Done!')
client.close()
