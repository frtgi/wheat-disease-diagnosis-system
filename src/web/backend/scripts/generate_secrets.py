"""
生成安全的密钥和密码
用于 WheatAgent 项目配置
"""
import secrets
import string
import hashlib

def generate_jwt_secret():
    """生成强 JWT 密钥"""
    return secrets.token_urlsafe(32)

def generate_database_password(length=16):
    """生成强数据库密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def generate_minio_credentials():
    """生成 MinIO 访问密钥和秘密密钥"""
    access_key = secrets.token_urlsafe(16)
    secret_key = secrets.token_urlsafe(32)
    return access_key, secret_key

def main():
    """主函数"""
    print("=" * 60)
    print("WheatAgent 安全密钥生成器")
    print("=" * 60)
    print()
    
    # 生成 JWT 密钥
    jwt_secret = generate_jwt_secret()
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()
    
    # 生成数据库密码
    db_password = generate_database_password()
    print(f"DATABASE_PASSWORD={db_password}")
    print()
    
    # 生成 MinIO 凭证
    minio_access, minio_secret = generate_minio_credentials()
    print(f"MINIO_ACCESS_KEY={minio_access}")
    print(f"MINIO_SECRET_KEY={minio_secret}")
    print()
    
    print("=" * 60)
    print("使用说明:")
    print("1. 复制以上密钥到您的 .env 文件")
    print("2. 切勿将 .env 文件提交到版本控制")
    print("3. 建议定期更新密钥")
    print("=" * 60)

if __name__ == "__main__":
    main()
