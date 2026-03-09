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
    print(out[:500]); print()

run('ss -tlnp | grep -E ":80|:443|:8080"')
run('docker ps --format "{{.Names}} {{.Ports}}" 2>/dev/null | head -10')

client.close()
