#!/bin/bash
set -e

echo "=== APS系统启动脚本 ==="

# Check MySQL
echo "等待MySQL..."
until mysqladmin ping -h"${DB_HOST:-localhost}" -u"${DB_USER:-aps_user}" -p"${DB_PASSWORD:-aps_password}" --silent 2>/dev/null; do
  sleep 2
done
echo "MySQL已就绪"

# Backend
cd /home/user/aps/backend
pip install -r requirements.txt -q

python seed_demo.py

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "后端启动 PID=$BACKEND_PID"

# Frontend
cd /home/user/aps/frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
echo "前端启动 PID=$FRONTEND_PID"

echo ""
echo "====================================="
echo "APS系统已启动"
echo "前端: http://localhost:5173"
echo "后端API: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "默认账户: admin / admin123"
echo "====================================="

wait $BACKEND_PID $FRONTEND_PID
