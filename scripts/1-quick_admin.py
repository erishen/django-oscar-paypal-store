#!/usr/bin/env python
"""
快速创建Django超级用户脚本
非交互式，支持环境变量或命令行参数
"""
import os
import sys
import django

# 添加Django项目路径
sys.path.insert(0, '/app/sandbox')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# 初始化Django
django.setup()

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

def create_admin(username, password, email=None):
    """创建或更新管理员用户"""
    try:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email or f'{username}@example.com',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )

        if created:
            user.set_password(password)
            user.save()
            print(f"✓ 创建管理员成功: {username}")
            return True
        else:
            # 如果用户已存在，更新密码
            user.set_password(password)
            user.email = email or f'{username}@example.com'
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            print(f"✓ 更新管理员成功: {username}")
            return True

    except ValidationError as e:
        print(f"✗ 创建管理员失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 创建管理员失败: {e}")
        return False

def list_admins():
    """列出所有管理员"""
    admins = User.objects.filter(is_staff=True)
    if admins.exists():
        print("\n=== 管理员列表 ===")
        for admin in admins:
            superuser = " (超级用户)" if admin.is_superuser else ""
            print(f"  - {admin.username}: {admin.email}{superuser}")
        print(f"总计: {admins.count()} 个管理员\n")
    else:
        print("\n未找到管理员用户\n")

def main():
    # 检查是否只是列出管理员
    if len(sys.argv) >= 2 and sys.argv[1] == '--list-only':
        list_admins()
        sys.exit(0)

    # 默认值
    DEFAULT_USERNAME = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
    DEFAULT_PASSWORD = os.environ.get('DJANGO_ADMIN_PASSWORD', 'admin123456')
    DEFAULT_EMAIL = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@example.com')

    # 支持命令行参数
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
        email = sys.argv[3] if len(sys.argv) >= 4 else None
    else:
        username = DEFAULT_USERNAME
        password = DEFAULT_PASSWORD
        email = DEFAULT_EMAIL

    print("=" * 50)
    print("Django Oscar 快速创建管理员")
    print("=" * 50)

    # 创建管理员
    success = create_admin(username, password, email)

    if success:
        print(f"\n登录信息:")
        print(f"  用户名: {username}")
        print(f"  密码: {password}")
        print(f"  后台地址: http://localhost:8080/admin/\n")

        # 列出所有管理员
        list_admins()
    else:
        print("\n管理员创建失败\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
