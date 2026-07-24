#!/usr/bin/env python
"""
数据统计脚本
"""
import os
import sys
import django

sys.path.insert(0, '/app/sandbox')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth import get_user_model
from oscar.apps.catalogue.models import (
    Product, ProductCategory, Category,
    ProductImage
)
from oscar.apps.partner.models import Partner, StockRecord
from oscar.apps.order.models import Order

User = get_user_model()

def print_stats():
    """打印数据统计"""
    print("\n" + "=" * 50)
    print("数据库数据统计")
    print("=" * 50)

    # 用户统计
    user_count = User.objects.count()
    admin_count = User.objects.filter(is_staff=True).count()
    print(f"\n👤 用户:")
    print(f"   总用户数: {user_count}")
    print(f"   管理员数: {admin_count}")

    # 产品统计
    product_count = Product.objects.count()
    parent_count = Product.objects.filter(parent=None).count()
    child_count = Product.objects.exclude(parent=None).count()
    print(f"\n📦 产品:")
    print(f"   总产品数: {product_count}")
    print(f"   父产品数: {parent_count}")
    print(f"   子产品数: {child_count}")

    # 分类统计
    category_count = Category.objects.count()
    product_category_count = ProductCategory.objects.count()
    print(f"\n📁 分类:")
    print(f"   分类总数: {category_count}")
    print(f"   产品分类关联: {product_category_count}")

    # 图片统计
    image_count = ProductImage.objects.count()
    print(f"\n🖼️  图片:")
    print(f"   产品图片数: {image_count}")

    # 库存统计
    stock_count = StockRecord.objects.count()
    print(f"\n📊 库存:")
    print(f"   库存记录数: {stock_count}")

    # 合作伙伴统计
    partner_count = Partner.objects.count()
    print(f"\n🏢 合作伙伴:")
    print(f"   合作伙伴数: {partner_count}")

    # 优惠统计 (Django Oscar offer 模块结构不同，暂时跳过)
    print(f"\n🎁 优惠:")
    print(f"   优惠数量: (暂未统计)")

    # 订单统计
    order_count = Order.objects.count()
    print(f"\n🛒 订单:")
    print(f"   订单数量: {order_count}")

    print("\n" + "=" * 50)

    # 检查关键数据
    print("\n数据检查:")

    if product_count > 0:
        print("✓ 产品数据已加载")
    else:
        print("✗ 产品数据未加载")

    if image_count > 0:
        print("✓ 产品图片已加载")
    else:
        print("⚠ 产品图片未加载（可能正常）")

    if stock_count > 0:
        print("✓ 库存数据已加载")
    else:
        print("✗ 库存数据未加载")

    # 优惠数据检查暂时跳过
    print("⚠ 优惠数据未检查")

    if category_count > 0:
        print("✓ 分类数据已加载")
    else:
        print("✗ 分类数据未加载")

    print("=" * 50 + "\n")

if __name__ == '__main__':
    print_stats()
