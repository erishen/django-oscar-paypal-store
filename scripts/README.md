# Scripts 目录

本目录包含 Django Oscar 项目的辅助管理脚本。

## 脚本列表

### Python 脚本

#### quick_admin.py
快速创建 Django 超级管理员。

**功能**：
- 非交互式创建管理员
- 支持环境变量配置
- 可更新已存在用户的密码

**用法**：
```bash
python /app/scripts/quick_admin.py                    # 默认 admin/admin123456
python /app/scripts/quick_admin.py username pass email  # 自定义创建
python /app/scripts/quick_admin.py --list-only   # 列出所有管理员
```

#### check_data.py
统计数据库中的数据信息。

**功能**：
- 统计用户、产品、分类、图片等数量
- 显示数据覆盖情况
- 检查关键数据是否已加载

**用法**：
```bash
python /app/scripts/check_data.py
```

**输出示例**：
```
============================================================
数据库数据统计
============================================================

👤 用户:
   总用户数: 1
   管理员数: 1

📦 产品:
   总产品数: 209
   父产品数: 88
   子产品数: 121
...
```

#### check_missing_images.py
检查缺失图片的产品。

**功能**：
- 查找所有没有图片的产品
- 按分类统计图片覆盖情况
- 列出缺失图片的产品详情

**用法**：
```bash
python /app/scripts/check_missing_images.py               # 基本检查
python /app/scripts/check_missing_images.py --category      # 按分类统计
```

#### add_default_images.py
为缺失图片的产品自动生成占位图。

**功能**：
- 为无图片产品生成白色背景占位图
- 占位图包含产品标题和边框
- 尺寸：800x600

**用法**：
```bash
python /app/scripts/add_default_images.py --dry-run      # 预览（不实际添加）
python /app/scripts/add_default_images.py --limit 10     # 只处理前10个
python /app/scripts/add_default_images.py               # 处理所有（需确认）
```

#### manage_search_index.py
搜索索引管理脚本。

**功能**：
- 重建搜索索引（清空后重建）
- 增量更新搜索索引
- 索引产品到 Elasticsearch

**用法**：
```bash
python /app/scripts/manage_search_index.py --rebuild      # 重建索引
python /app/scripts/manage_search_index.py --update       # 增量更新
python /app/scripts/manage_search_index.py                # 默认重建
```

### Shell 脚本

#### init_products.sh
产品数据完整初始化脚本。

**功能**：
1. 加载子产品数据
2. 导入CSV产品数据（所有CSV文件）
3. 导入产品图片
4. 加载国家数据
5. 加载页面数据
6. 加载分类和优惠数据
7. 重建搜索索引

**用法**：
```bash
bash /app/scripts/init_products.sh
```

**注意**：
- 脚本会跳过已失败的操作继续执行
- 每个步骤都有错误提示

## Docker 集成

这些脚本已集成到 Dockerfile 中：

```dockerfile
COPY scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh && \
    chown -R django:django /app/scripts/
```

## Makefile 命令

所有脚本都可通过 Makefile 命令调用：

| Makefile 命令 | 对应脚本 | 说明 |
|--------------|---------|------|
| `make quick-admin` | quick_admin.py | 快速创建管理员 |
| `make list-admins` | quick_admin.py | 列出所有管理员 |
| `make create-admin` | quick_admin.py | 自定义创建管理员 |
| `make check-data` | check_data.py | 查看数据统计 |
| `make check-images` | check_missing_images.py | 检查图片 |
| `make check-images-detail` | check_missing_images.py | 按分类检查 |
| `make add-placeholder-images` | add_default_images.py | 预览占位图 |
| `make add-placeholder-images-10` | add_default_images.py | 添加10个占位图 |
| `make add-all-placeholder-images` | add_default_images.py | 添加所有占位图 |
| `make init-products` | init_products.sh | 初始化产品数据 |
| `make rebuild-index` | manage_search_index.py | 重建搜索索引 |
| `make update-index` | manage_search_index.py | 增量更新索引 |


## 注意事项

1. **Python 路径**：所有 Python 脚本使用 `/app/sandbox` 作为项目路径
2. **Django 设置**：脚本自动设置 `DJANGO_SETTINGS_MODULE='settings'`
3. **错误处理**：脚本有基本的错误处理，失败会继续执行下一步
4. **权限**：Shell 脚本在 Dockerfile 中设置了执行权限

## 扩展

如需添加新脚本：
1. 创建 `.py` 或 `.sh` 文件
2. 添加可执行权限（Shell 脚本）
3. 在 Dockerfile 中复制到 `/app/scripts/`
4. 在 Makefile 中添加对应命令
