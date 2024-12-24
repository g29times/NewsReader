import bcrypt
import secrets
import string

def generate_salt() -> bytes:
    """生成密码盐值"""
    return bcrypt.gensalt()

def hash_password(password: str) -> str:
    """对密码进行加密"""
    # 生成盐值并加密密码
    salt = generate_salt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def generate_random_password(length: int = 12) -> str:
    """生成随机密码"""
    # 定义字符集
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # 生成随机密码
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password
