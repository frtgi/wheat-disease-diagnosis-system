# 数据库快速启动指南

## 快速开始（5 分钟完成）

### 方式一：使用 SQL 脚本（最简单）

```bash
# 1. 执行初始化脚本
mysql -u root -p < d:/Project/wheatagent/src/database/init.sql

# 2. 验证
mysql -u root -p -e "USE wheat_agent_db; SHOW TABLES; SELECT COUNT(*) FROM users;"
```

### 方式二：使用 Python 脚本

```bash
# 1. 确保后端依赖已安装
cd d:/Project/wheatagent/src/web/backend
pip install -r requirements.txt

# 2. 配置数据库连接
# 编辑 src/web/backend/app/core/config.py
# 修改 DATABASE_URL 为你的数据库连接信息

# 3. 运行迁移脚本
cd d:/Project/wheatagent
python src/database/migrations/001_initial.py
```

## 测试数据库连接

### 测试用户登录

使用以下测试账号登录（密码均为：`123456`）：

- **农户账号**: `farmer_zhang` / `zhang@example.com`
- **农技人员账号**: `tech_wang` / `wang@example.com`
- **管理员账号**: `admin` / `admin@example.com`

### API 测试

```bash
# 1. 启动后端服务
cd d:/Project/wheatagent/src/web/backend
python -m uvicorn app.main:app --reload

# 2. 访问 API 文档
# 浏览器打开：http://localhost:8000/docs

# 3. 测试登录接口
POST http://localhost:8000/api/v1/user/login
Content-Type: application/json

{
  "username": "farmer_zhang",
  "password": "123456"
}
```

## 数据库表概览

```
wheat_agent_db/
├── users (用户表) - 5 条测试数据
├── diseases (病害表) - 5 条测试数据
├── diagnoses (诊断记录表) - 5 条测试数据
├── knowledge_graph (知识图谱表) - 20 条测试数据
├── v_diagnosis_detail (视图)
└── v_disease_stats (视图)
```

## 包含的病害数据

1. ✅ 小麦条锈病 - 真菌性病害
2. ✅ 小麦叶锈病 - 真菌性病害
3. ✅ 小麦白粉病 - 真菌性病害
4. ✅ 小麦赤霉病 - 真菌性病害
5. ✅ 小麦纹枯病 - 真菌性病害

## 常用 SQL 查询

### 查看所有用户
```sql
SELECT id, username, email, role, phone FROM users;
```

### 查看所有病害
```sql
SELECT id, name, category, severity FROM diseases;
```

### 查看诊断记录详情
```sql
SELECT * FROM v_diagnosis_detail LIMIT 10;
```

### 查看病害统计
```sql
SELECT * FROM v_disease_stats;
```

## 故障排查

### 问题：无法连接数据库

**解决方案**：
1. 检查 MySQL 服务是否启动
2. 检查数据库连接配置
3. 确认用户名密码正确

### 问题：SQL 脚本执行失败

**解决方案**：
```bash
# 手动登录 MySQL 执行
mysql -u root -p
mysql> source d:/Project/wheatagent/src/database/init.sql;
```

### 问题：Python 迁移脚本报错

**解决方案**：
```bash
# 检查依赖是否安装
pip install sqlalchemy pymysql

# 检查数据库配置
# 编辑 src/web/backend/app/core/config.py
```

## 下一步

数据库初始化完成后，可以：

1. ✅ 启动后端服务：`python -m uvicorn app.main:app --reload`
2. ✅ 启动前端服务：`cd frontend && npm run dev`
3. ✅ 访问应用：`http://localhost:5173`
4. ✅ 测试诊断功能
5. ✅ 查看 API 文档：`http://localhost:8000/docs`

## 相关文档

- 📖 [完整数据库文档](README.md)
- 📖 [Web 架构设计](../../../docs/WEB_ARCHITECTURE.md)
- 📖 [API 接口文档](../../../docs/API_REFERENCE.md)
- 📖 [spec.md](../../../.trae/specs/web-development/spec.md)
