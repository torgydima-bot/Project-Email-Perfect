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

cmd = r'''cd /var/www/email-perfect && venv/bin/python3 -c "
import httpx
from playwright.sync_api import sync_playwright

url = 'https://perfect-org.ru/asconodum'

# Test 1: httpx raw
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
resp = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
print('=== HTTPX ===')
print('Status:', resp.status_code)
print('Final URL:', str(resp.url))
print('Raw HTML (first 1000):')
print(resp.text[:1000])
print()

# Test 2: Playwright full page text
print('=== PLAYWRIGHT ===')
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=30000, wait_until='domcontentloaded')
    page.wait_for_timeout(3000)
    content = page.content()
    text = page.inner_text('body')
    browser.close()
print('Content length:', len(content))
print('Body text (first 1000):')
print(text[:1000])
"
'''

stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace').strip()
err = stderr.read().decode('utf-8', errors='replace').strip()
print(out[:3000])
if err:
    print('ERR:', err[:500])

client.close()
