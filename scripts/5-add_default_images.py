#!/usr/bin/env python
"""
为缺失图片的产品添加默认占位图
"""
import os
import sys
import django

sys.path.insert(0, '/app/sandbox')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from oscar.apps.catalogue.models import Product, ProductImage, ProductClass
from django.core.files import File
from django.db.models import Count
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

def create_placeholder_image(title, width=800, height=600):
    """创建占位图"""
    # 创建白色背景
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # 添加边框
    border_width = 10
    draw.rectangle(
        [(border_width, border_width), (width-border_width, height-border_width)],
        outline='#E0E0E0',
        width=border_width
    )
    
    # 添加标题
    font_size = 40
    if len(title) > 30:
        font_size = 30
    
    # 简单的字体处理
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size)
    except:
        font = ImageFont.load_default()
    
    # 文字换行
    words = title.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        text_width = draw.textlength(test_line, font=font)
        
        if text_width > width - 100:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # 绘制文字
    total_text_height = len(lines) * (font_size + 10)
    start_y = (height - total_text_height) // 2
    
    for i, line in enumerate(lines):
        text_width = draw.textlength(line, font=font)
        x = (width - text_width) // 2
        y = start_y + i * (font_size + 10)
        draw.text((x, y), line, fill='#333333', font=font)
    
    # 保存到内存
    img_io = BytesIO()
    img.save(img_io, format='JPEG', quality=90)
    img_io.seek(0)
    return img_io

def add_default_images(limit=None, dry_run=False):
    """为缺失图片的产品添加默认图片"""
    print("=" * 60)
    print("为缺失图片的产品添加默认占位图")
    print("=" * 60)
    
    # 查找缺失图片的产品
    missing_products = Product.objects.annotate(img_count=Count('images')).filter(img_count=0)
    
    if limit:
        missing_products = missing_products[:limit]
    
    print(f"\n找到 {missing_products.count()} 个缺失图片的产品")
    
    if dry_run:
        print("\n[预览模式] 不会实际添加图片")
    
    added = 0
    skipped = 0
    
    for i, product in enumerate(missing_products, 1):
        print(f"\n[{i}/{missing_products.count()}] {product.title}")
        print(f"  UPC: {product.upc or 'N/A'}")
        
        if dry_run:
            print("  [预览] 将添加占位图")
            added += 1
            continue
        
        try:
            # 创建占位图
            img_io = create_placeholder_image(product.title)
            
            # 生成文件名
            filename = f"placeholder_{product.id if product.id else i}.jpg"
            
            # 创建 ProductImage
            product_image = ProductImage()
            product_image.product = product
            product_image.original.save(
                filename,
                File(img_io),
                save=True
            )
            
            # 显示为默认图片
            product_image.display_order = 0
            product_image.save()
            
            print(f"  ✓ 已添加占位图: {filename}")
            added += 1
            
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            skipped += 1
    
    print("\n" + "=" * 60)
    print(f"完成! 添加: {added}, 跳过: {skipped}")
    print("=" * 60)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--dry-run':
        add_default_images(dry_run=True)
    elif len(sys.argv) > 1 and sys.argv[1] == '--limit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        add_default_images(limit=limit)
    else:
        print("\n⚠️  警告: 这将为所有缺失图片的产品添加占位图")
        print("使用 --dry-run 先预览")
        print("使用 --limit N 限制处理数量")
        
        confirm = input("\n确定要继续吗? (yes/no): ")
        if confirm.lower() == 'yes':
            add_default_images()
        else:
            print("操作已取消")

if __name__ == '__main__':
    main()
