# WheatAgent 项目冗余检查与数据库设计审查报告

**审查日期**: 2026-04-21  
**审查范围**: 10 个 ORM 模型 / 10 个 SQL 表 / 30 个服务文件 / 13 个路由文件  
**发现问题**: 25 个（高: 7 / 中: 11 / 低: 7）  
**建议清理**: 可删除 2 个冗余文件，可合并 6 组重复代码，需修复 7 个高优先级问题  

---

## 执行摘要

本次审查覆盖 WheatAgent 项目的数据库设计、ORM 模型与 SQL 脚本一致性、认证安全性、以及代码冗余等方面。主要发现：

1. **ORM 与 SQL 存在多处不一致**：字段类型不匹配、迁移脚本与 ORM 定义冲突、SQL 脚本引用了不存在的表名
2. **认证表存在安全隐患**：RefreshToken 验证存在明文回退逻辑、UserSession 令牌明文存储、LoginAttempt 无自动清理机制
3. **数据冗余问题**：disease_name 在 diagnoses 和 diagnosis_confidences 表中冗余存储
4. **代码冗余**：32 个重复函数名、GPU 监控模块重复、缓存实现分散

---

## 一、冗余代码和文件

### 1.1 后端路由重复 [低]

| 文件 A | 文件 B | 重复内容 | 建议操作 |
|--------|--------|---------|---------|
| `app/api/v1/ai_diagnosis.py` | `app/api/v1/diagnosis_router.py` | ai_diagnosis.py 是薄包装层，仅重新导出 diagnosis_router 的 router | 版本升级时移除 ai_diagnosis.py，统一使用 diagnosis_router.py |

### 1.2 服务层重复 [中]

| 重复类型 | 文件 A | 文件 B | 重复函数/类 | 建议操作 |
|---------|--------|--------|-----------|---------|
| GPU 监控 | `app/core/gpu_monitor.py` | `app/utils/gpu_monitor.py` | 整个模块重复 | 保留 core 版本，删除 utils 版本 |
| 缓存实现 | `app/services/cache.py` (CacheService) | `app/services/cache_manager.py` (CacheManager) | `get_stats`, `invalidate_user_cache` 等功能重叠 | 统一为单一缓存服务 |
| 缓存实现 | `app/services/cache_manager.py` | `app/services/inference_cache_service.py` | `get`, `set`, `delete`, `clear`, `get_stats` 功能重叠 | 合并为统一缓存层 |
| 模型管理 | `app/services/model_manager.py` | `app/services/qwen/qwen_loader.py` | `load_model`, `unload_model`, `get_model_status` | qwen_loader 是专用实现，model_manager 是通用接口，保留两者但消除方法签名重复 |
| 登录记录 | `app/services/auth.py` | `app/services/cache.py` | `record_login_attempt` | auth.py 写 DB，cache.py 写 Redis，职责不同但函数名重复，建议重命名 cache.py 版本 |
| 诊断日志 | `app/services/diagnosis_logger.py` | `app/services/diagnosis_logger.py` | `log_diagnosis` 在同一文件中定义两次（L65 和 L308） | 删除重复定义 |

### 1.3 临时文件清理 [低]

| 文件路径 | 类型 | 大小 | 建议操作 |
|---------|------|------|---------|
| `tests/coverage.xml` | 测试报告 | 431.9 KB | 加入 .gitignore |
| `src/web/backend/scripts/reports/*.json` (10 个) | 集成测试报告 | ~50 KB | 加入 .gitignore 或定期清理 |
| `src/web/backend/scripts/v46_screenshots/*.png` (13 个) | 截图文件 | ~2 MB | 加入 .gitignore |
| `src/web/backend/utils/hardware_analysis_result.json` | 硬件分析结果 | 小 | 加入 .gitignore |
| `src/web/backend/utils/model_architecture_result.json` | 模型架构结果 | 小 | 加入 .gitignore |
| `src/web/backend/scripts/hardware_bottleneck_result.json` | 瓶颈分析结果 | 小 | 加入 .gitignore |

### 1.4 配置文件冗余 [低]

| 文件 A | 文件 B | 重复配置 | 建议操作 |
|--------|--------|---------|---------|
| `configs/wheat_agent.yaml` | `configs/wheat_disease.yaml` | 数据集类别定义相同 | 合并为统一配置 |
| `configs/training_v9.yaml` | `configs/training_v10_yolov8s.yaml` | 训练参数重叠 | 保留最新版本，归档旧版 |
| YAML 配置系统 | Python Settings 类 | 双配置系统并存 | 统一为 Python Settings 类 |

---

## 二、数据库设计审查

### 2.1 ORM 与 SQL 一致性 [高]

| 表名 | 问题类型 | 详细说明 | 严重程度 |
|------|---------|---------|---------|
| `knowledge_graph` | 字段类型不匹配 | ORM: `id = Column(Integer)` vs SQL: `id BIGINT PRIMARY KEY`。知识图谱数据量大，ORM 的 Integer 可能溢出 | **高** |
| `diseases` | SQL 缺失字段 | ORM 有 `code`(VARCHAR(50), unique)、`severity`(Float)、`is_active`(Boolean) 字段，SQL init.sql 中缺失 | **高** |
| `users` | SQL 缺失字段 | ORM 有 `deleted_at`(DateTime)、`last_login_at`(DateTime) 字段，SQL init.sql 中缺失（迁移 002 添加） | **中** |
| `diagnoses` | 迁移与 ORM 冲突 | 迁移 002 将 `confidence` 重命名为 `primary_confidence`，但 ORM 仍使用 `confidence`。若执行迁移会导致 ORM 字段映射失败 | **高** |
| `diagnoses` | 迁移与 ORM 冲突 | 迁移 002 删除 `disease_name` 字段，但 ORM 仍保留该字段。若执行迁移会导致 ORM 写入失败 | **高** |
| `audit_logs` | 孤儿表 | 迁移 002 创建了 `audit_logs` 表，但无对应 ORM 模型，无法通过 ORM 访问 | **中** |
| `add_indexes.sql` | 表名错误 | 使用 `diagnosis_records` 而非 `diagnoses`，执行此脚本会导致 SQL 错误 | **高** |
| `refresh_tokens` | 字段长度不一致 | ORM: `token = Column(String(128))` vs 迁移 001: `sa.String(255)`。ORM 定义更严格，但迁移脚本更宽松 | **中** |
| `password_reset_tokens` | 索引命名不一致 | ORM: `ix_pwdreset_user_token_unique` vs 迁移 002: `uq_pwdreset_user_token`。同一约束在不同位置使用不同名称 | **低** |

### 2.2 表结构设计问题 [中]

| 表名 | 问题类型 | 详细说明 | 建议修改 |
|------|---------|---------|---------|
| 所有表 | 主键索引冗余 | `id = Column(Integer, primary_key=True, index=True)` — InnoDB 主键自动创建聚簇索引，`index=True` 是冗余的 | 移除主键字段的 `index=True` |
| `login_attempts` | 缺少外键 | `username` 字段存储用户名而非 `user_id`，无法与 users 表建立外键关系。用户删除后记录成为孤儿数据 | 添加 `user_id` 外键字段，保留 `username` 作为快照 |
| `user_sessions` | 令牌明文存储 | `session_token` 以明文 VARCHAR(255) 存储，与 `refresh_tokens` 的 SHA256 哈希存储策略不一致 | 对 session_token 进行 SHA256 哈希后存储 |
| `password_reset_tokens` | 缺少 updated_at | 无 `updated_at` 字段，无法追踪令牌状态变更时间 | 添加 `updated_at` 字段 |
| `refresh_tokens` | 缺少 updated_at | 无 `updated_at` 字段，撤销操作无时间记录 | 添加 `updated_at` 字段 |
| `user_sessions` | 缺少 updated_at | 无 `updated_at` 字段，会话状态变更无时间记录 | 添加 `updated_at` 字段 |
| 所有表 | datetime.utcnow 已弃用 | Python 3.12+ 中 `datetime.utcnow()` 已弃用，应使用 `datetime.now(timezone.utc)` | 统一替换为 `datetime.now(timezone.utc)` |
| `diagnoses` | 软删除与硬删除并存 | ORM 定义了 `deleted_at` 软删除字段，但路由层 `delete_diagnosis_record` 使用 `db.delete(record)` 硬删除 | 统一为软删除策略 |

### 2.3 数据一致性 [中]

| 表名 | 字段 | 问题描述 | 建议修改 |
|------|------|---------|---------|
| `diagnoses` | `disease_name` | 冗余字段：当 `disease_id` 非空时，`disease_name` 与 `diseases.name` 重复存储。若 Disease 名称更新，diagnoses 中的旧名称不会同步 | 保留作为快照（诊断时固化），但需在代码注释中明确设计意图 |
| `diagnosis_confidences` | `disease_name` | 同上，与 `diseases.name` 冗余存储 | 同上，保留作为诊断快照 |
| `diagnoses` | `recommendations` | ORM 定义为 JSON 类型，但路由代码中使用 `json.dumps()` 序列化后写入，导致双重序列化 | 统一使用 ORM 的 JSON 类型自动序列化，移除手动 `json.dumps()` |
| `diseases` | `code` | ORM 中定义了 `code` 字段（unique, index），但 SQL init.sql 中缺失 | 在 SQL init.sql 中补充 `code` 字段定义 |
| `diseases` | `severity` | ORM 中定义了 `severity` 字段（Float, index），但 SQL init.sql 中缺失 | 在 SQL init.sql 中补充 `severity` 字段定义 |
| `diseases` | `is_active` | ORM 中定义了 `is_active` 字段（Boolean, index），但 SQL init.sql 中缺失 | 在 SQL init.sql 中补充 `is_active` 字段定义 |

### 2.4 安全性审查 [高]

| 表名 | 问题 | 风险等级 | 建议修改 |
|------|------|---------|---------|
| `refresh_tokens` | **verify_refresh_token 存在明文回退逻辑**：先尝试 SHA256 哈希匹配，失败后回退到明文匹配（auth.py L326-332）。这削弱了哈希存储的安全意义，攻击者若获取数据库可直接使用明文令牌 | **高** | 移除明文回退逻辑，仅支持哈希验证。如需兼容旧数据，添加数据迁移脚本将明文令牌转为哈希 |
| `user_sessions` | **session_token 明文存储**：与 refresh_tokens 的 SHA256 哈希存储策略不一致。若数据库泄露，攻击者可直接使用 session_token 劫持会话 | **高** | 对 session_token 进行 SHA256 哈希后存储，验证时先哈希再比对 |
| `login_attempts` | **无自动清理机制**：当前 107 条记录，模型注释建议"90 天清理"，但无实际实现。数据将持续增长 | **中** | 添加定时任务清理 90 天前的记录，或使用 MySQL EVENT 自动清理 |
| `refresh_tokens` | **过期/撤销令牌未清理**：当前 182 条记录，无清理策略。已过期和已撤销的令牌持续占用存储 | **中** | 添加定时任务清理已过期且已撤销的令牌（保留未过期撤销令牌用于安全审计） |
| `password_reset_tokens` | **已使用令牌未清理**：当前 0 条记录（使用率低），但已使用的令牌无清理策略 | **低** | 添加定时任务清理已使用且过期的令牌 |
| `user_sessions` | **过期会话未清理**：当前仅 1 条记录，但无自动清理过期会话的机制 | **低** | 添加定时任务清理过期会话 |

---

## 三、数据库表使用情况分析

| 表名 | 记录数 | 分析 | 建议 |
|------|--------|------|------|
| `users` | 6 | 正常，测试用户+管理员 | - |
| `diseases` | 14 | 正常，覆盖主要小麦病害 | - |
| `diagnoses` | 6 | 使用率低，可能因为诊断记录主要通过 SSE 流保存 | 检查 SSE 流保存逻辑是否正常 |
| `diagnosis_confidences` | 6 | 与 diagnoses 1:1 对应，正常 | - |
| `knowledge_graph` | 10 | 数据量偏少，仅覆盖基础三元组 | 扩充知识图谱数据 |
| `image_metadata` | 0 | **从未使用**，图像上传后未创建元数据记录 | 检查上传流程，确保创建 ImageMetadata 记录 |
| `password_reset_tokens` | 0 | 正常，密码重置功能使用率低 | - |
| `refresh_tokens` | 182 | **数据量异常偏高**，可能存在令牌泄漏或未正确撤销 | 1. 检查登录流程是否正确撤销旧令牌；2. 清理过期令牌 |
| `login_attempts` | 107 | **数据量偏高**，无清理机制导致持续增长 | 添加 90 天清理策略 |
| `user_sessions` | 1 | 使用率极低，可能未正确创建会话 | 检查登录流程是否正确创建 UserSession |

---

## 四、修复建议优先级

### 高优先级（立即修复）

1. **修复 add_indexes.sql 中的表名错误**：将 `diagnosis_records` 改为 `diagnoses`，否则执行脚本会报错
2. **修复迁移 002 与 ORM 的冲突**：迁移 002 将 `confidence` 重命名为 `primary_confidence` 并删除 `disease_name`，但 ORM 仍使用原始字段名。需统一：要么回滚迁移中的重命名操作，要么更新 ORM 模型
3. **修复 knowledge_graph.id 类型不匹配**：ORM 使用 Integer（32位，最大 2^31-1），SQL 使用 BIGINT（64位）。知识图谱数据量大，应将 ORM 改为 `BigInteger`
4. **移除 RefreshToken 验证的明文回退逻辑**：auth.py 中 `verify_refresh_token` 和 `revoke_refresh_token` 函数在哈希匹配失败后回退到明文匹配，削弱了哈希存储的安全性
5. **对 UserSession.session_token 进行哈希存储**：与 RefreshToken 保持一致的安全策略
6. **补充 SQL init.sql 中缺失的 diseases 表字段**：`code`、`severity`、`is_active`
7. **修复 diagnoses 表 recommendations 字段的双重序列化问题**：路由代码中手动 `json.dumps()` 与 ORM 的 JSON 类型冲突

### 中优先级（规划修复）

1. **为 audit_logs 表创建 ORM 模型**：迁移 002 创建了该表但无 ORM 映射，导致无法通过应用层访问
2. **为 login_attempts 添加 user_id 外键**：当前仅存储 username 字符串，无法与 users 表关联
3. **添加认证表的 updated_at 字段**：PasswordResetToken、RefreshToken、UserSession 缺少更新时间戳
4. **实现 LoginAttempt 自动清理机制**：添加定时任务清理 90 天前的记录
5. **实现 RefreshToken 过期清理机制**：清理已过期且已撤销的令牌
6. **统一缓存服务实现**：合并 CacheService（cache.py）和 CacheManager（cache_manager.py），消除功能重叠
7. **修复 delete_diagnosis_record 的硬删除问题**：改为软删除（设置 deleted_at）
8. **替换 datetime.utcnow 为 datetime.now(timezone.utc)**：Python 3.12+ 兼容性
9. **检查 image_metadata 表为何无数据**：上传流程可能未正确创建元数据记录
10. **检查 refresh_tokens 182 条记录的合理性**：可能存在令牌未正确撤销的问题
11. **统一 refresh_tokens.token 字段长度**：ORM String(128) vs 迁移 String(255)

### 低优先级（逐步清理）

1. **移除 ai_diagnosis.py 薄包装层**：统一使用 diagnosis_router.py
2. **删除重复的 GPU 监控模块**：保留 `app/core/gpu_monitor.py`，移除 `app/utils/gpu_monitor.py`
3. **清理临时报告文件**：将测试报告、截图等加入 .gitignore
4. **合并重复的数据集配置文件**：wheat_agent.yaml 和 wheat_disease.yaml
5. **统一索引命名规范**：password_reset_tokens 和 refresh_tokens 的复合唯一约束命名不一致
6. **移除主键字段的冗余 index=True**：InnoDB 主键自动创建聚簇索引
7. **归档旧版训练配置**：training_v7.yaml、training_v8.yaml 已在 archive 目录，确认不再使用

---

## 五、附录：ORM 与 SQL 字段详细对比

### 5.1 diseases 表差异

| 字段 | ORM 定义 | SQL init.sql | 状态 |
|------|---------|-------------|------|
| `code` | `String(50), unique, index` | ❌ 缺失 | **需补充** |
| `severity` | `Float, index` | ❌ 缺失 | **需补充** |
| `is_active` | `Boolean, index` | ❌ 缺失 | **需补充** |
| `prevention_methods` | `JSON` | `JSON` | ✅ 一致 |
| `treatment_methods` | `JSON` | `JSON` | ✅ 一致 |

### 5.2 knowledge_graph 表差异

| 字段 | ORM 定义 | SQL init.sql | 状态 |
|------|---------|-------------|------|
| `id` | `Integer` | `BIGINT` | **类型不匹配** |

### 5.3 diagnoses 表迁移冲突

| 字段 | ORM 定义 | 迁移 002 操作 | 状态 |
|------|---------|-------------|------|
| `confidence` | `DECIMAL(5,4)` | 重命名为 `primary_confidence` | **冲突** |
| `disease_name` | `String(100)` | 删除该字段 | **冲突** |

---

*报告生成时间: 2026-04-21*  
*审查工具: project-audit-redundancy-db-review 技能 + 人工深度审查*
