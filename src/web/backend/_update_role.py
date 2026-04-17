import pymysql
conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', database='wheat_agent_db')
cur = conn.cursor()
cur.execute("UPDATE users SET role='admin' WHERE username='v21test_admin'")
conn.commit()
cur.execute("SELECT username, role FROM users WHERE username='v21test_admin'")
print(cur.fetchone())
conn.close()
