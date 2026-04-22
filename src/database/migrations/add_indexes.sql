-- ====================================================
-- IWDDA 小麦病害诊断系统数据库索引优化迁移脚本
-- ====================================================
-- 版本：v1.1
-- 日期：2026-03-10
-- 说明：为高频查询字段添加索引以提升查询性能
-- ====================================================

USE wheat_agent_db;

-- ====================================================
-- 1. 诊断记录表索引优化
-- ====================================================
-- 添加病害名称索引（用于统计和筛选）
ALTER TABLE `diagnoses` ADD INDEX `idx_disease_name` (`disease_name`);

-- 添加状态索引（用于筛选未完成的诊断）
ALTER TABLE `diagnoses` ADD INDEX `idx_status` (`status`);

-- 添加生长阶段索引（用于生长阶段分析）
ALTER TABLE `diagnoses` ADD INDEX `idx_growth_stage` (`growth_stage`);

-- ====================================================
-- 2. 病害数据表索引优化
-- ====================================================
-- 病害名称已经索引，添加分类索引
-- 注意：idx_category 已存在，无需重复添加

-- ====================================================
-- 3. 知识图谱表索引优化
-- ====================================================
-- 添加复合索引：实体类型 + 实体（用于知识图谱查询）
ALTER TABLE `knowledge_graph` ADD INDEX `idx_entity_type_entity` (`entity_type`, `entity`);

-- 添加目标实体索引（用于关系查询）
ALTER TABLE `knowledge_graph` ADD INDEX `idx_target_entity` (`target_entity`);

-- ====================================================
-- 4. 用户表索引优化
-- ====================================================
-- 添加角色索引（用于用户筛选和权限管理）
ALTER TABLE `users` ADD INDEX `idx_role` (`role`);

-- 添加活跃度索引（用于筛选活跃用户）
ALTER TABLE `users` ADD INDEX `idx_is_active` (`is_active`);

-- ====================================================
-- 5. 诊断记录表复合索引
-- ====================================================
-- 添加复合索引：用户 ID + 创建时间（用于用户历史查询）
ALTER TABLE `diagnoses` ADD INDEX `idx_user_created` (`user_id`, `created_at`);

-- 添加复合索引：病害名称 + 创建时间（用于病害趋势分析）
ALTER TABLE `diagnoses` ADD INDEX `idx_disease_created` (`disease_name`, `created_at`);

-- ====================================================
-- 6. 验证索引创建
-- ====================================================
SELECT '索引优化完成！' as message;

-- 显示所有表的索引信息
SHOW INDEX FROM `users`;
SHOW INDEX FROM `diagnoses`;
SHOW INDEX FROM `diseases`;
SHOW INDEX FROM `knowledge_graph`;

-- ====================================================
-- 7. 性能对比查询（可选）
-- ====================================================
-- 以下查询可用于测试索引效果

-- 查询 1: 按用户 ID 和时间查询诊断记录（使用 idx_user_created）
-- EXPLAIN SELECT * FROM diagnoses WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10;

-- 查询 2: 按病害名称统计（使用 idx_disease_name）
-- EXPLAIN SELECT disease_name, COUNT(*) FROM diagnoses GROUP BY disease_name;

-- 查询 3: 知识图谱实体查询（使用 idx_entity_type_entity）
-- EXPLAIN SELECT * FROM knowledge_graph WHERE entity_type = 'disease' AND entity = '白粉病';

-- 查询 4: 按角色筛选用户（使用 idx_role）
-- EXPLAIN SELECT * FROM users WHERE role = 'technician';
