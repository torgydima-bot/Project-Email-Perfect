#!/bin/bash
# Запускать на сервере: bash setup_server.sh
set -e

APP_DIR=/var/www/email-perfect
APP_USER=www-data

echo "=== 1. Обновление пакетов ==="
apt update -y && apt install -y python3 python3-pip python3-venv nginx

echo "=== 2. Создание директории ==="
mkdir -p $APP_DIR
mkdir -p $APP_DIR/static/uploads
chown -R $APP_USER:$APP_USER $APP_DIR

echo "=== 3. Виртуальное окружение ==="
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== 4. Инициализация базы данных ==="
python3 -c "from app import create_app; from db.models import db; app=create_app(); app.app_context().push(); db.create_all(); print('БД создана')"

echo "=== 5. Systemd сервис ==="
cat > /etc/systemd/system/email-perfect.service << 'EOF'
[Unit]
Description=Email Perfect Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/email-perfect
Environment="PATH=/var/www/email-perfect/venv/bin"
ExecStart=/var/www/email-perfect/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5001 --timeout 300 wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable email-perfect
systemctl restart email-perfect

echo "=== 6. Nginx конфиг ==="
cat > /etc/nginx/sites-available/email-perfect << 'EOF'
server {
    listen 8080;
    server_name _;
    client_max_body_size 32M;

    location /static/ {
        alias /var/www/email-perfect/static/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/email-perfect /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo ""
echo "=== ГОТОВО ==="
echo "Приложение доступно на: http://77.73.233.5:8080"
echo "Статус сервиса: systemctl status email-perfect"
