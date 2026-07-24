#!/bin/bash
# 产品数据初始化脚本

echo "=========================================="
echo "Django Oscar 产品数据初始化"
echo "=========================================="

cd /app/sandbox

# 1. 加载子产品数据
echo "1/7 - 加载子产品数据..."
python manage.py loaddata fixtures/child_products.json || echo "  ✗ 子产品数据加载失败"

# 2. 导入CSV格式产品数据
echo "2/7 - 导入CSV产品数据..."
for csv_file in fixtures/*.csv; do
    if [ -f "$csv_file" ]; then
        echo "  正在导入: $csv_file"
        python manage.py oscar_import_catalogue "$csv_file" || echo "  ✗ $csv_file 导入失败"
    fi
done

# 3. 导入产品图片
echo "3/7 - 导入产品图片..."
if [ -f fixtures/images.tar.gz ]; then
    python manage.py oscar_import_catalogue_images fixtures/images.tar.gz || echo "  ✗ 产品图片导入失败"
else
    echo "  ⚠ 图片文件不存在: fixtures/images.tar.gz"
fi

# 4. 加载国家数据（用于地址）
echo "4/7 - 加载国家数据..."
python manage.py oscar_populate_countries --initial-only || echo "  ✗ 国家数据加载失败"

# 5. 加载页面数据
echo "5/7 - 加载页面数据..."
python manage.py loaddata fixtures/pages.json || echo "  ✗ 页面数据加载失败"

# 6. 加载商品分类和优惠数据
echo "6/7 - 加载分类和优惠数据..."
python manage.py loaddata fixtures/ranges.json || echo "  ✗ 分类数据加载失败"
python manage.py loaddata fixtures/offers.json || echo "  ✗ 优惠数据加载失败"

# 7. 重建搜索索引
echo "7/7 - 重建搜索索引..."
python manage.py clear_index --noinput || echo "  ✗ 清除索引失败"
python manage.py update_index catalogue || echo "  ✗ 建立索引失败"

echo "=========================================="
echo "产品数据初始化完成!"
echo "=========================================="

# 显示产品统计
echo ""
echo "=== 数据统计 ==="
python /app/check_data.py || echo "  无法统计数据"
