#!/bin/bash

echo "🚧 Instalando dependências de sistema..."
sudo apt update
sudo apt install -y python3.10-venv unixodbc-dev curl gnupg software-properties-common

echo "📦 Instalando ODBC Driver da Microsoft..."
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository "$(wget -qO- https://packages.microsoft.com/config/ubuntu/22.04/prod.list)"
sudo apt update
sudo apt install -y msodbcsql17

echo "🐍 Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Instalando requirements do projeto..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🧪 Instalando gunicorn se ainda não estiver no requirements..."
pip install gunicorn

echo "📂 Garantindo que a pasta de logs existe..."
mkdir -p logs

echo "🚀 Iniciando Gunicorn na porta 8000..."
nohup gunicorn DisparadorBack.wsgi:application \
  --bind 0.0.0.0:8000 \
  --timeout 600 \
  --workers 3 > logs/Bot.log 2>&1 &

echo "✅ Backend rodando em http://localhost:8000"
