#!/bin/bash

echo "🔍 Verificando processo anterior na porta 8000..."
PID=$(lsof -ti:8000)

if [ -n "$PID" ]; then
  echo "🛑 Finalizando processo anterior com PID $PID..."
  kill -9 $PID
else
  echo "✅ Nenhum processo antigo na porta 8000."
fi

echo "📂 Garantindo que a pasta de logs existe..."
mkdir -p logs

echo "🚀 Iniciando Gunicorn com Django..."
source venv/bin/activate
nohup gunicorn DisparadorBack.wsgi:application \
  --bind 0.0.0.0:8000 \
  --timeout 600 \
  --workers 3 > logs/Bot.log 2>&1 &

echo "✅ Backend iniciado com sucesso!"
