#!/usr/bin/env python
"""
搜索索引管理脚本
用于重建和更新搜索索引
"""
import os
import sys
import django

sys.path.insert(0, '/app/sandbox')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

def rebuild_index():
    """重建搜索索引"""
    import subprocess
    
    print("=" * 50)
    print("重建搜索索引")
    print("=" * 50)
    print()
    
    # 清空索引
    print("步骤 1/2: 清空现有索引...")
    result = subprocess.run(
        ['python', '/app/sandbox/manage.py', 'clear_index', '--noinput'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("错误:", result.stderr)
        return False
    
    # 重建索引
    print("\n步骤 2/2: 重建索引...")
    result = subprocess.run(
        ['python', '/app/sandbox/manage.py', 'update_index', 'catalogue'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("错误:", result.stderr)
        return False
    
    print("\n" + "=" * 50)
    print("✅ 搜索索引重建完成!")
    print("=" * 50)
    return True

def update_index():
    """增量更新索引"""
    import subprocess
    
    print("=" * 50)
    print("增量更新搜索索引")
    print("=" * 50)
    print()
    
    result = subprocess.run(
        ['python', '/app/sandbox/manage.py', 'update_index', 'catalogue'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("错误:", result.stderr)
        return False
    
    print("\n" + "=" * 50)
    print("✅ 搜索索引更新完成!")
    print("=" * 50)
    return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='搜索索引管理')
    parser.add_argument('--rebuild', action='store_true', help='重建索引（清空后重建）')
    parser.add_argument('--update', action='store_true', help='增量更新索引')
    
    args = parser.parse_args()
    
    if args.rebuild:
        rebuild_index()
    elif args.update:
        update_index()
    else:
        # 默认重建
        rebuild_index()
