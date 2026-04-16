# 数据库迁移指南

本文档介绍小麦病害 AI 诊断系统的数据库初始化和迁移方法。

## 目录结构

```
src/database/
├── init.sql              # SQL 初始化脚本（直接执行）
├── migrations/           # Python 迁移脚本
│   └── 001_initial.py    # 初始迁移（创建表 + 插入数据）
└── README.md             # 本文档
```

## 方法一：使用 SQL 脚本初始化（推荐）

### 步骤

1. **登录 MySQL**
   ```bash
   mysql -u root -p
   ```

2. **执行初始化脚本**
   ```sql
   source d:/Project/wheatagent/src/database/init.sql;
   ```

   或者在命令行直接执行：
   ```bash
   mysql -u root -p < d:/Project/wheatagent/src/database/init.sql
   ```

3. **验证数据库**
   ```sql
   USE wheat_agent_db;
   SHOW TABLES;
   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM diseases;
   ```

### 包含内容

- ✅ 创建数据库 `wheat_agent_db`
- ✅ 创建 4 张表：users, diseases, diagnoses, knowledge_graph
- ✅ 创建索引和外键约束
- ✅ 插入 5 个测试用户
- ✅ 插入 5 种常见小麦病害
- ✅ 插入 15 条知识图谱数据
- ✅ 插入 5 条示例诊断记录
- ✅ 创建 2 个视图：v_diagnosis_detail, v_disease_stats

## 方法二：使用 Python 迁移脚本

### 前提条件

确保已安装所需依赖：

```bash
cd d:/Project/wheatagent/src/web/backend
pip install -r requirements.txt
```

### 步骤

1. **配置数据库连接**

   编辑 `src/web/backend/app/core/config.py`，确保数据库连接正确：

   ```python
   DATABASE_URL = "mysql+pymysql://root:your_password@localhost:3306/wheat_agent_db"
   ```

2. **运行迁移脚本**
   ```bash
   cd d:/Project/wheatagent
   python src/database/migrations/001_initial.py
   ```

3. **验证迁移结果**
   ```bash
   mysql -u root -p -e "USE wheat_agent_db; SELECT * FROM users;"
   ```

### 回滚迁移

如需删除所有数据（慎用）：

```bash
python src/database/migrations/001_initial.py --downgrade
```

## 数据库表结构

### 1. users 表（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| username | VARCHAR(50) | 用户名，唯一索引 |
| email | VARCHAR(100) | 邮箱，唯一索引 |
| password_hash | VARCHAR(255) | 密码哈希 |
| role | ENUM | 角色：farmer/technician/admin |
| phone | VARCHAR(20) | 手机号 |
| avatar_url | VARCHAR(255) | 头像 URL |
| is_active | BOOLEAN | 是否激活 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**索引**: idx_username, idx_email

### 2. diseases 表（病害表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| name | VARCHAR(100) | 病害名称，索引 |
| scientific_name | VARCHAR(100) | 学名 |
| code | VARCHAR(50) | 疾病编码，唯一 |
| category | ENUM | 分类：fungal/bacterial/viral/pest/nutritional |
| symptoms | TEXT | 症状描述 |
| description | TEXT | 详细描述 |
| causes | TEXT | 病因 |
| prevention_methods | TEXT | 预防方法 (JSON) |
| treatment_methods | TEXT | 治疗方法 (JSON) |
| suitable_growth_stage | VARCHAR(100) | 适用生长阶段 |
| image_urls | TEXT | 图片 URL(JSON) |
| severity | FLOAT | 严重程度 (0-1) |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**索引**: idx_name, idx_category

### 3. diagnoses 表（诊断记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| user_id | INT | 用户 ID，外键，索引 |
| disease_id | INT | 疾病 ID，外键，索引 |
| image_url | VARCHAR(255) | 诊断图像 URL |
| symptoms | TEXT | 症状描述 |
| disease_name | VARCHAR(100) | 病害名称 |
| confidence | DECIMAL(5,4) | 置信度 |
| severity | VARCHAR(20) | 严重程度 |
| description | TEXT | 诊断描述 |
| recommendations | TEXT | 防治建议 (JSON) |
| growth_stage | VARCHAR(50) | 生长阶段 |
| weather_data | TEXT | 天气数据 (JSON) |
| location | VARCHAR(100) | 地理位置 |
| status | VARCHAR(20) | 状态：pending/completed |
| created_at | TIMESTAMP | 创建时间，索引 |
| updated_at | TIMESTAMP | 更新时间 |

**外键**: 
- fk_diagnoses_user → users(id) ON DELETE CASCADE
- fk_diagnoses_disease → diseases(id) ON DELETE SET NULL

**索引**: idx_user_id, idx_disease_id, idx_created_at

### 4. knowledge_graph 表（知识图谱表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| entity | VARCHAR(100) | 实体名称，索引 |
| entity_type | ENUM | 实体类型：disease/symptom/pest/treatment/growth_stage |
| relation | VARCHAR(100) | 关系类型，索引 |
| target_entity | VARCHAR(100) | 目标实体 |
| attributes | TEXT | 实体属性 (JSON) |
| created_at | TIMESTAMP | 创建时间 |

**索引**: idx_entity, idx_entity_type, idx_relation

## 测试数据

### 默认用户（密码均为：123456）

| 用户名 | 邮箱 | 角色 |
|--------|------|------|
| farmer_zhang | zhang@example.com | farmer |
| farmer_li | li@example.com | farmer |
| tech_wang | wang@example.com | technician |
| tech_zhao | zhao@example.com | technician |
| admin | admin@example.com | admin |

### 包含的病害种类

1. 小麦条锈病 (WD001) - 真菌性
2. 小麦叶锈病 (WD002) - 真菌性
3. 小麦白粉病 (WD003) - 真菌性
4. 小麦赤霉病 (WD004) - 真菌性
5. 小麦纹枯病 (WD005) - 真菌性

## 视图

### v_diagnosis_detail 视图

诊断记录详情视图，关联用户信息：

```sql
SELECT 
    d.id AS diagnosis_id,
    d.user_id,
    u.username,
    d.disease_id,
    d.disease_name,
    d.confidence,
    d.severity,
    d.description,
    d.growth_stage,
    d.location,
    d.status,
    d.created_at
FROM diagnoses d
LEFT JOIN users u ON d.user_id = u.id
ORDER BY d.created_at DESC;
```

### v_disease_stats 视图

病害统计视图，统计每种病害的诊断次数和平均置信度：

```sql
SELECT 
    ds.id,
    ds.name,
    ds.category,
    ds.severity AS disease_severity,
    COUNT(d.id) AS diagnosis_count,
    AVG(d.confidence) AS avg_confidence
FROM diseases ds
LEFT JOIN diagnoses d ON ds.id = d.disease_id
GROUP BY ds.id, ds.name, ds.category, ds.severity;
```

## 常见问题

### 1. 数据库连接失败

检查数据库连接配置：
```python
# src/web/backend/app/core/config.py
DATABASE_URL = "mysql+pymysql://root:your_password@localhost:3306/wheat_agent_db"
```

### 2. 外键约束错误

确保按正确顺序创建表（或使用 `SET FOREIGN_KEY_CHECKS = 0`）

### 3. 字符集问题

确保使用 utf8mb4 字符集：
```sql
SHOW CREATE DATABASE wheat_agent_db;
SHOW CREATE TABLE users;
```

### 4. 权限不足

确保数据库用户有足够权限：
```sql
GRANT ALL PRIVILEGES ON wheat_agent_db.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

## 后续迁移

如需添加新的迁移脚本，请按以下格式：

```
src/database/migrations/
├── 001_initial.py      # 初始迁移
├── 002_add_column.py   # 添加字段
└── 003_update_data.py  # 更新数据
```

每个迁移脚本应包含：
- `upgrade()` 函数：执行迁移
- `downgrade()` 函数：回滚迁移

## 相关文档

- [spec.md](../../../.trae/specs/web-development/spec.md) - Web 开发规格文档
- [WEB_ARCHITECTURE.md](../../../docs/WEB_ARCHITECTURE.md) - Web 架构设计文档
- [API_REFERENCE.md](../../../docs/API_REFERENCE.md) - API 接口文档
