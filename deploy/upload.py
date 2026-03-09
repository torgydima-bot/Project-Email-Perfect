import paramiko
import os

APP_LOCAL = r"c:\Projects Claude Code\Project Email Perfect"
APP_REMOTE = "/var/www/email-perfect"
HOST = "77.73.233.5"
USER = "root"
PASS = "fuJyBtG*96(Y"

SKIP_DIRS = {'.git', '__pycache__', 'deploy'}
SKIP_FILES = {'.pyc', '.db'}

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
sftp = client.open_sftp()

files_to_upload = []
for root, dirs, files in os.walk(APP_LOCAL):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for fname in files:
        if any(fname.endswith(ext) for ext in SKIP_FILES):
            continue
        local_path = os.path.join(root, fname)
        rel_path = os.path.relpath(local_path, APP_LOCAL).replace(os.sep, '/')
        remote_path = APP_REMOTE + '/' + rel_path
        files_to_upload.append((local_path, remote_path))

print(f'Files to upload: {len(files_to_upload)}')

def ensure_dir(sftp, path):
    parts = path.rsplit('/', 1)
    if len(parts) < 2:
        return
    parent = parts[0]
    dirs = []
    p = parent
    while p and p != '/':
        dirs.append(p)
        p = p.rsplit('/', 1)[0] if '/' in p else ''
    for d in reversed(dirs):
        try:
            sftp.mkdir(d)
        except:
            pass

uploaded = 0
errors = 0
for local_path, remote_path in files_to_upload:
    ensure_dir(sftp, remote_path)
    try:
        sftp.put(local_path, remote_path)
        uploaded += 1
        if uploaded % 20 == 0:
            print(f'  Uploaded: {uploaded}/{len(files_to_upload)}')
    except Exception as e:
        print(f'  ERROR {remote_path}: {e}')
        errors += 1

print(f'Done! Uploaded {uploaded}, errors: {errors}')
sftp.close()
client.close()
