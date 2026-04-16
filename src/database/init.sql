-- ====================================================
-- IWDDA 小麦病害诊断系统数据库初始化脚本
-- ====================================================
-- 数据库：wheat_agent_db
-- 版本：v1.0
-- 生成日期：2026-03-10
-- ====================================================

-- 创建数据库
DROP DATABASE IF EXISTS wheat_agent_db;
CREATE DATABASE wheat_agent_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE wheat_agent_db;

-- ====================================================
-- 1. 创建用户表
-- ====================================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户 ID',
  `username` VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
  `email` VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `role` ENUM('farmer', 'technician', 'admin') DEFAULT 'farmer' COMMENT '角色',
  `phone` VARCHAR(20) COMMENT '手机号',
  `avatar_url` VARCHAR(255) COMMENT '头像 URL',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否激活',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_username` (`username`),
  INDEX `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ====================================================
-- 2. 创建病害数据表
-- ====================================================
DROP TABLE IF EXISTS `diseases`;

CREATE TABLE `diseases` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '病害 ID',
  `name` VARCHAR(100) NOT NULL COMMENT '病害名称',
  `scientific_name` VARCHAR(100) COMMENT '学名',
  `category` ENUM('fungal', 'bacterial', 'viral', 'pest', 'nutritional') NOT NULL COMMENT '分类',
  `symptoms` TEXT NOT NULL COMMENT '症状描述',
  `description` TEXT COMMENT '详细描述',
  `prevention_methods` JSON COMMENT '防治方法',
  `treatment_methods` JSON COMMENT '治疗方法',
  `suitable_growth_stage` VARCHAR(100) COMMENT '适宜生长阶段',
  `image_urls` JSON COMMENT '图片 URL 列表',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_name` (`name`),
  INDEX `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='病害数据表';

-- ====================================================
-- 3. 创建诊断记录表
-- ====================================================
DROP TABLE IF EXISTS `diagnosis_records`;

CREATE TABLE `diagnosis_records` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '诊断记录 ID',
  `user_id` INT NOT NULL COMMENT '用户 ID',
  `image_url` VARCHAR(255) NOT NULL COMMENT '图像 URL',
  `disease_name` VARCHAR(100) NOT NULL COMMENT '病害名称',
  `confidence` DECIMAL(5,4) NOT NULL COMMENT '置信度',
  `severity` VARCHAR(20) COMMENT '严重程度',
  `description` TEXT COMMENT '诊断描述',
  `recommendations` JSON COMMENT '防治建议',
  `growth_stage` VARCHAR(50) COMMENT '生长阶段',
  `weather_data` JSON COMMENT '天气数据',
  `location` VARCHAR(100) COMMENT '位置',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='诊断记录表';

-- ====================================================
-- 4. 创建知识图谱表
-- ====================================================
DROP TABLE IF EXISTS `knowledge_graph`;

CREATE TABLE `knowledge_graph` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '知识 ID',
  `entity` VARCHAR(100) NOT NULL COMMENT '实体名称',
  `entity_type` ENUM('disease', 'symptom', 'pest', 'treatment', 'growth_stage') NOT NULL COMMENT '实体类型',
  `relation` VARCHAR(100) COMMENT '关系',
  `target_entity` VARCHAR(100) COMMENT '目标实体',
  `attributes` JSON COMMENT '属性',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_entity` (`entity`),
  INDEX `idx_entity_type` (`entity_type`),
  INDEX `idx_relation` (`relation`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识图谱表';

-- ====================================================
-- 5. 插入测试数据
-- ====================================================

-- 5.1 插入测试用户（密码均为：123456，bcrypt 哈希）
INSERT INTO `users` (`username`, `email`, `password_hash`, `role`, `phone`) VALUES
('farmer_zhang', 'zhang@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'farmer', '13800138001'),
('farmer_li', 'li@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'farmer', '13800138002'),
('tech_wang', 'wang@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'technician', '13800138003'),
('tech_zhao', 'zhao@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'technician', '13800138004'),
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'admin', '13800138005');

-- 5.2 插入常见小麦病害数据
INSERT INTO `diseases` (`name`, `scientific_name`, `category`, `symptoms`, `description`, `prevention_methods`, `treatment_methods`) VALUES
('白粉病', 'Blumeria graminis', 'fungal', 
'叶片表面出现白色粉状斑点，逐渐扩大形成白色粉层，严重时叶片变黄枯死。',
'白粉病是小麦常见病害，主要危害叶片，也可危害叶鞘、茎秆和穗部。',
'["选用抗病品种", "合理密植", "科学施肥", "及时排水"],
'["喷洒三唑酮可湿性粉剂", "使用烯唑醇", "喷施多菌灵"]'),

('锈病', 'Puccinia striiformis', 'fungal',
'叶片表面出现黄色或褐色粉状孢子堆，呈条状或椭圆形排列。',
'锈病是小麦重要病害，分为条锈、叶锈和秆锈三种类型。',
'["选用抗病品种", "适期播种", "合理施肥", "清除自生麦"],
'["喷洒粉锈宁", "使用烯唑醇", "喷施三唑酮"]'),

('赤霉病', 'Fusarium graminearum', 'fungal',
'穗部受害，小穗颖片呈水渍状淡褐色，后产生粉红色霉层。',
'赤霉病是小麦穗部重要病害，影响产量和品质。',
'["选用抗病品种", "合理轮作", "及时排水", "适期收获"],
'["喷洒多菌灵", "使用甲基托布津", "喷施咪鲜胺"]'),

('纹枯病', 'Rhizoctonia cerealis', 'fungal',
'叶鞘出现椭圆形病斑，边缘褐色，中央淡褐色或灰白色。',
'纹枯病主要危害叶鞘和叶片，严重时导致植株倒伏。',
'["合理密植", "科学施肥", "及时排水", "清除病残体"],
'["喷洒井冈霉素", "使用多抗霉素", "喷施噻呋酰胺"]'),

('蚜虫', 'Sitobion avenae', 'pest',
'叶片背面和嫩茎上聚集绿色或黑色小虫，吸食汁液，叶片卷曲。',
'蚜虫是小麦常见害虫，群集危害，传播病毒病。',
'["保护天敌", "黄板诱杀", "合理施肥", "及时灌溉"],
'["喷洒吡虫啉", "使用啶虫脒", "喷施高效氯氰菊酯"]');

-- 5.3 插入知识图谱数据
INSERT INTO `knowledge_graph` (`entity`, `entity_type`, `relation`, `target_entity`, `attributes`) VALUES
('白粉病', 'disease', 'HAS_SYMPTOM', '白色粉状斑点', '{"severity": "high"}'),
('白粉病', 'disease', 'TREATED_BY', '三唑酮', '{"effectiveness": 0.9}'),
('白粉病', 'disease', 'TREATED_BY', '烯唑醇', '{"effectiveness": 0.85}'),
('锈病', 'disease', 'HAS_SYMPTOM', '黄色粉状孢子堆', '{"severity": "high"}'),
('锈病', 'disease', 'TREATED_BY', '粉锈宁', '{"effectiveness": 0.95}'),
('赤霉病', 'disease', 'HAS_SYMPTOM', '穗部粉红色霉层', '{"severity": "very_high"}'),
('赤霉病', 'disease', 'TREATED_BY', '多菌灵', '{"effectiveness": 0.88}'),
('纹枯病', 'disease', 'HAS_SYMPTOM', '叶鞘椭圆形病斑', '{"severity": "medium"}'),
('蚜虫', 'pest', 'TREATED_BY', '吡虫啉', '{"effectiveness": 0.92}'),
('蚜虫', 'pest', 'TREATED_BY', '啶虫脒', '{"effectiveness": 0.90}');

-- ====================================================
-- 6. 创建视图（可选）
-- ====================================================

-- 6.1 诊断详情视图
DROP VIEW IF EXISTS `v_diagnosis_detail`;

CREATE VIEW `v_diagnosis_detail` AS
SELECT 
    dr.id,
    dr.user_id,
    u.username,
    dr.disease_name,
    dr.confidence,
    dr.severity,
    dr.created_at
FROM diagnosis_records dr
JOIN users u ON dr.user_id = u.id;

-- 6.2 病害统计视图
DROP VIEW IF EXISTS `v_disease_stats`;

CREATE VIEW `v_disease_stats` AS
SELECT 
    disease_name,
    COUNT(*) as total_count,
    AVG(confidence) as avg_confidence
FROM diagnosis_records
GROUP BY disease_name;

-- ====================================================
-- 7. 完成提示
-- ====================================================
SELECT '数据库初始化完成！' as message;
SELECT CONCAT('用户数：', COUNT(*)) as message FROM users;
SELECT CONCAT('病害数：', COUNT(*)) as message FROM diseases;
SELECT CONCAT('知识图谱条目数：', COUNT(*)) as message FROM knowledge_graph;
