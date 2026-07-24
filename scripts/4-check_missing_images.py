#!/usr/bin/env python
"""
检查和处理缺失图片的产品
"""
import os
import sys
import django

sys.path.insert(0, '/app/sandbox')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from oscar.apps.catalogue.models import Product, ProductImage
from django.db.models import Count, Q

def check_missing_images():
    """检查缺失图片的产品"""
    print("=" * 60)
    print("产品图片检查报告")
    print("=" * 60)
    
    # 统计
    total_products = Product.objects.count()
    products_with_images = Product.objects.annotate(img_count=Count('images')).filter(img_count__gt=0).count()
    products_without_images = Product.objects.annotate(img_count=Count('images')).filter(img_count=0).count()
    
    print(f"\n📊 统计信息:")
    print(f"  总产品数: {total_products}")
    print(f"  有图片的产品: {products_with_images}")
    print(f"  无图片的产品: {products_without_images}")
    print(f"  覆盖率: {products_with_images/total_products*100:.1f}%")
    
    # 显示缺失图片的产品
    if products_without_images > 0:
        print(f"\n❌ 缺失图片的产品列表 (前20个):")
        print("-" * 60)
        
        missing_products = Product.objects.annotate(img_count=Count('images')).filter(img_count=0)[:20]
        
        for i, product in enumerate(missing_products, 1):
            print(f"\n{i}. {product.title}")
            print(f"   UPC: {product.upc or 'N/A'}")
            print(f"   类别: {product.get_product_class().name if product.get_product_class() else 'N/A'}")
            print(f"   父产品: {product.parent.title if product.parent else 'N/A'}")
            
            # 显示是否有描述
            has_description = bool(product.description)
            has_short_desc = bool(product.get_attribute_values())
            print(f"   有描述: {'是' if has_description else '否'}")
            print(f"   有属性: {'是' if has_short_desc else '否'}")
    
    print("\n" + "=" * 60)
    
    return {
        'total': total_products,
        'with_images': products_with_images,
        'without_images': products_without_images,
        'coverage': products_with_images/total_products*100 if total_products > 0 else 0
    }

def list_products_by_category():
    """按分类统计图片覆盖情况"""
    print("\n📁 按分类统计:")
    print("-" * 60)
    
    categories = Product.objects.values_list(
        'product_class__name',
        flat=True
    ).distinct()
    
    for category in categories:
        if not category:
            continue
            
        products_in_category = Product.objects.filter(product_class__name=category)
        total = products_in_category.count()
        
        with_images = products_in_category.annotate(
            img_count=Count('images')
        ).filter(img_count__gt=0).count()
        
        coverage = with_images / total * 100 if total > 0 else 0
        
        status = "✅" if coverage >= 80 else "⚠️" if coverage >= 50 else "❌"
        print(f"{status} {category}:")
        print(f"   总计: {total} | 有图片: {with_images} | 覆盖率: {coverage:.1f}%")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--category':
        check_missing_images()
        list_products_by_category()
    else:
        stats = check_missing_images()
        
        if stats['coverage'] >= 80:
            print("\n✅ 图片覆盖率良好")
        elif stats['coverage'] >= 50:
            print("\n⚠️  建议补充更多图片")
        else:
            print("\n❌ 图片覆盖不足，建议尽快补充")
        
        print("\n提示: 使用 --category 参数查看按分类统计")
        print("      在管理后台 http://localhost:8080/admin/ 为产品添加图片")

if __name__ == '__main__':
    main()
