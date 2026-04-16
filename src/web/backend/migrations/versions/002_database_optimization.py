"""database comprehensive optimization

Revision ID: 002
Revises: 001
Create Date: 2026-04-03 00:00:00.000000

数据库全面优化迁移脚本：

新增表（3张）：
- diagnosis_confidences: 诊断多候选置信度表
- image_metadata: 图像元数据表
- audit_logs: 操作审计日志表

现有表变更：
- diagnoses: 移除冗余字段、重命名、新增FK/JSON字段/软删除/索引
- users: 新增 deleted_at, last_login_at 及复合索引
- diseases: Text→JSON类型升级 + is_active + 复合索引
- knowledge_graph: Text→JSON类型升级 + 新复合索引
- password_reset_tokens: 添加 (user_id, token) 复合唯一约束
- refresh_tokens: 添加 (user_id, token) 复合唯一约束
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级数据库架构
    
    执行以下操作：
    1. 创建3张新表
    2. 修改现有表结构（字段增删改、类型升级）
    3. 创建新的索引和约束
    """
    
    # ========================================
    # Part 1: 创建新表
    # ========================================
    
    # --- 1.1 diagnosis_confidences 表 ---
    op.create_table(
        'diagnosis_confidences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='置信度记录 ID'),
        sa.Column('diagnosis_id', sa.Integer(), nullable=False, comment='关联诊断记录 ID'),
        sa.Column('disease_name', sa.String(100), nullable=False, comment='病害名称'),
        sa.Column('confidence', sa.DECIMAL(5, 4), nullable=False, comment='置信度 (0-1)'),
        sa.Column('disease_class', sa.Integer(), nullable=True, comment='病害类别 ID (YOLO类别索引)'),
        sa.Column('rank', sa.Integer(), nullable=False, server_default=sa.text("'0'"), comment='排序序号 (0=最高置信度)'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['diagnosis_id'], ['diagnoses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_comment='诊断多候选置信度表'
    )
    op.create_index(op.f('ix_diagnosis_confidences_id'), 'diagnosis_confidences', ['id'], unique=False)
    op.create_index('idx_diagconf_diagnosis_confidence', 'diagnosis_confidences', ['diagnosis_id', sa.text('confidence DESC')])
    op.create_index('idx_diagconf_disease_name', 'diagnosis_confidences', ['disease_name'])
    
    # --- 1.2 image_metadata 表 ---
    op.create_table(
        'image_metadata',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='图像 ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='上传用户 ID'),
        sa.Column('hash_value', sa.String(64), nullable=False, comment='图像 SHA256 哈希值（用于去重）'),
        sa.Column('original_filename', sa.String(255), nullable=False, comment='原始文件名'),
        sa.Column('file_path', sa.String(500), nullable=False, comment='存储路径'),
        sa.Column('file_size', sa.Integer(), nullable=False, comment='文件大小（字节）'),
        sa.Column('mime_type', sa.String(50), nullable=True, comment='MIME 类型（如 image/jpeg）'),
        sa.Column('width', sa.Integer(), nullable=True, comment='图像宽度（像素）'),
        sa.Column('height', sa.Integer(), nullable=True, comment='图像高度（像素）'),
        sa.Column('storage_provider', sa.Enum('local', 'minio', name='storage_provider'), server_default='local', comment="存储提供者"),
        sa.Column('is_processed', sa.Boolean(), server_default=sa.text("'0'"), comment='是否已处理（用于诊断标记）'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='上传时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_comment='图像元数据表'
    )
    op.create_index(op.f('ix_image_metadata_id'), 'image_metadata', ['id'], unique=False)
    op.create_unique_index('ix_image_metadata_hash_value', 'image_metadata', ['hash_value'])
    op.create_index('idx_image_user_created', 'image_metadata', ['user_id', 'created_at'])
    
    # --- 1.3 audit_logs 表 ---
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='日志 ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='操作用户 ID（系统操作为 NULL）'),
        sa.Column('action', sa.Enum(
            'login', 'logout', 'register', 'password_change', 'password_reset',
            'role_update', 'data_create', 'data_update', 'data_delete',
            'admin_action', 'diagnosis_request', 'token_refresh',
            name='audit_action'
        ), nullable=False, comment='操作类型'),
        sa.Column('resource_type', sa.String(50), nullable=True, comment='资源类型（如 user/diagnosis/disease）'),
        sa.Column('resource_id', sa.Integer(), nullable=True, comment='资源 ID'),
        sa.Column('ip_address', sa.String(45), nullable=True, comment='操作 IP 地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='客户端 User-Agent'),
        sa.Column('details', sa.JSON(), nullable=True, comment='操作详情（JSON 格式）'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='操作时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_comment='操作审计日志表'
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index('idx_audit_user_action_created', 'audit_logs', ['user_id', 'action', 'created_at'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_action_created', 'audit_logs', ['action', 'created_at'])
    
    # ========================================
    # Part 2: 修改现有表结构
    # ========================================
    
    # --- 2.1 diagnoses 表变更 ---
    with op.batch_alter_table('diagnoses', schema=None) as batch_op:
        # 删除冗余字段 disease_name（如果有）
        batch_op.drop_column('disease_name', existing_type=sa.String(100), existing_nullable=True)
        
        # 重命名 confidence -> primary_confidence
        batch_op.alter_column('confidence', new_column_name='primary_confidence',
                             existing_type=sa.Float(), existing_nullable=True)
        
        # 新增字段
        batch_op.add_column(sa.Column('image_id', sa.Integer(), nullable=True, comment='关联图像元数据 ID'))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'))
        
        # 类型升级: Text -> JSON
        batch_op.alter_column('recommendations', existing_type=sa.Text(),
                             type_=sa.JSON(), existing_nullable=True,
                             postgresql_using="recommendations::json")
        batch_op.alter_column('weather_data', existing_type=sa.Text(),
                             type_=sa.JSON(), existing_nullable=True,
                             postgresql_using="weather_data::json")
        
        # 添加外键约束
        batch_op.create_foreign_key('fk_diagnoses_image_id', 'image_metadata', ['image_id'], ['id'],
                                    ondelete='SET NULL')
        
        # 添加新索引
        batch_op.create_index('idx_user_status_created', ['user_id', 'status', 'created_at'])
        batch_op.create_index('idx_location', ['location'])
        batch_op.create_index('idx_diag_deleted', ['deleted_at'])
    
    # --- 2.2 users 表变更 ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        # 新增字段
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True,
                                     comment='软删除时间（NULL 表示未删除）'))
        batch_op.add_column(sa.Column('last_login_at', sa.DateTime(), nullable=True,
                                     comment='最后登录时间'))
        
        # 添加复合索引
        batch_op.create_index('idx_users_active_deleted', ['is_active', 'deleted_at'])
    
    # --- 2.3 diseases 表变更 ---
    with op.batch_alter_table('diseases', schema=None) as batch_op:
        # 类型升级: Text -> JSON
        batch_op.alter_column('prevention_methods', existing_type=sa.Text(),
                             type_=sa.JSON(), existing_nullable=True,
                             postgresql_using="prevention_methods::json")
        batch_op.alter_column('treatment_methods', existing_type=sa.Text(),
                             type_=sa.JSON(), existing_nullable=True,
                             postgresql_using="treatment_methods::json")
        batch_op.alter_column('image_urls', existing_type=sa.Text(),
                             type_=sa.JSON(), existing_nullable=True,
                             postgresql_using="image_urls::json")
        
        # 新增字段
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default=sa.text("'1'"),
                                     comment='是否启用'))
        
        # 添加复合索引
        batch_op.create_index('idx_disease_category_active_severity', 
                             ['category', 'is_active', 'severity'])
    
    # --- 2.4 knowledge_graph 表变更 ---
    with op.batch_alter_table('knowledge_graph', schema=None) as batch_op:
        # 类型升级: Text -> JSON
        batch_op.alter_column('attributes', existing_type=sa.Text(),
                             type_=sa.JSON(), existing_nullable=True,
                             postgresql_using="attributes::json")
        
        # 添加复合索引
        batch_op.create_index('idx_kg_entity_type_entity', ['entity_type', 'entity'])
        batch_op.create_index('idx_kg_relation_target', ['relation', 'target_entity'])
    
    # --- 2.5 auth 表添加复合唯一约束 ---
    with op.batch_alter_table('password_reset_tokens', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_pwdreset_user_token', ['user_id', 'token'])
    
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_reftoken_user_token', ['user_id', 'token'])


def downgrade() -> None:
    """
    回滚数据库架构
    
    按照与 upgrade 相反的顺序执行回滚操作。
    """
    
    # ========================================
    # 回滚 auth 表约束
    # ========================================
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.drop_constraint('uq_reftoken_user_token', type_='unique')
    
    with op.batch_alter_table('password_reset_tokens', schema=None) as batch_op:
        batch_op.drop_constraint('uq_pwdreset_user_token', type_='unique')
    
    # ========================================
    # 回滚 knowledge_grid 表变更
    # ========================================
    with op.batch_alter_table('knowledge_graph', schema=None) as batch_op:
        batch_op.drop_index('idx_kg_relation_target')
        batch_op.drop_index('idx_kg_entity_type_entity')
        batch_op.alter_column('attributes', existing_type=sa.JSON(),
                             type_=sa.Text(), existing_nullable=True)
    
    # ========================================
    # 回滚 diseases 表变更
    # ========================================
    with op.batch_alter_table('diseases', schema=None) as batch_op:
        batch_op.drop_index('idx_disease_category_active_severity')
        batch_op.drop_column('is_active')
        batch_op.alter_column('image_urls', existing_type=sa.JSON(),
                             type_=sa.Text(), existing_nullable=True)
        batch_op.alter_column('treatment_methods', existing_type=sa.JSON(),
                             type_=sa.Text(), existing_nullable=True)
        batch_op.alter_column('prevention_methods', existing_type=sa.JSON(),
                             type_=sa.Text(), existing_nullable=True)
    
    # ========================================
    # 回滚 users 表变更
    # ========================================
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('idx_users_active_deleted')
        batch_op.drop_column('last_login_at')
        batch_op.drop_column('deleted_at')
    
    # ========================================
    # 回滚 diagnoses 表变更
    # ========================================
    with op.batch_alter_table('diagnoses', schema=None) as batch_op:
        batch_op.drop_index('idx_diag_deleted')
        batch_op.drop_index('idx_location')
        batch_op.drop_index('idx_user_status_created')
        batch_op.drop_constraint('fk_diagnoses_image_id', type_='foreignkey')
        batch_op.alter_column('weather_data', existing_type=sa.JSON(),
                             type_=sa.Text(), existing_nullable=True)
        batch_op.alter_column('recommendations', existing_type=sa.JSON(),
                             type_=sa.Text(), existing_nullable=True)
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('image_id')
        batch_op.alter_column('primary_confidence', new_column_name='confidence',
                             existing_type=sa.DECIMAL(5, 4), existing_nullable=True)
        batch_op.add_column(sa.Column('disease_name', sa.String(100), nullable=True))
    
    # ========================================
    # 删除新表
    # ========================================
    op.drop_index('idx_audit_action_created', table_name='audit_logs')
    op.drop_index('idx_audit_resource', table_name='audit_logs')
    op.drop_index('idx_audit_user_action_created', table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('idx_image_user_created', table_name='image_metadata')
    op.drop_index('ix_image_metadata_hash_value', table_name='image_metadata')
    op.drop_index(op.f('ix_image_metadata_id'), table_name='image_metadata')
    op.drop_table('image_metadata')
    
    op.drop_index('idx_diagconf_disease_name', table_name='diagnosis_confidences')
    op.drop_index('idx_diagconf_diagnosis_confidence', table_name='diagnosis_confidences')
    op.drop_index(op.f('ix_diagnosis_confidences_id'), table_name='diagnosis_confidences')
    op.drop_table('diagnosis_confidences')
