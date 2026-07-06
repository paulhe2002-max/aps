#!/bin/sh
set -e

echo "等待 MySQL 就绪..."
until python -c "
import pymysql, os, sys
try:
    pymysql.connect(
        host=os.getenv('DB_HOST','mysql'),
        port=int(os.getenv('DB_PORT',3306)),
        user=os.getenv('DB_USER','aps_user'),
        password=os.getenv('DB_PASSWORD','aps_password'),
        database=os.getenv('DB_NAME','aps_db_1'),
    )
    print('MySQL 已就绪')
except Exception as e:
    print(f'等待中: {e}')
    sys.exit(1)
"; do
  sleep 2
done

echo "初始化数据库表..."
python -c "from app.database import create_tables; create_tables(); print('表初始化完成')"

echo "导入演示数据..."
python seed_demo.py || echo "演示数据已存在，跳过"

echo "启动后端服务..."
exec uvicorn app.main:app --host 0.0.0.0 --port 9000
