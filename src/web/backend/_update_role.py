import os
import pymysql

db_password = os.environ.get('DB_PASSWORD', '')
if not db_password:
    print("错误：请设置 DB_PASSWORD 环境变量")
    exit(1)
conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password=db_password, database='wheat_agent_db')
cur = conn.cursor()
cur.execute("UPDATE users SET role='admin' WHERE username='v21test_admin'")
conn.commit()
cur.execute("SELECT username, role FROM users WHERE username='v21test_admin'")
print(cur.fetchone())
conn.close()
