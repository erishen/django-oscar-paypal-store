# Django Oscar 产品数据管理指南

## 概述

本文档介绍如何初始化和管理 Django Oscar 项目的产品数据。

## 快速开始

### 1. 重新构建镜像（首次使用）

由于添加了新脚本，需要重新构建镜像：

```bash
cd /path/to/django-oscar-research
make build
make up
```

### 2. 自动初始化（推荐）

首次启动时，`init-db.sh` 会自动加载所有产品数据，包括：
- ✅ 用户数据（管理员和普通用户）
- ✅ 产品数据（父子产品）
- ✅ 产品图片
- ✅ 国家数据
- ✅ 页面数据
- ✅ 分类和优惠
- ✅ 示例订单
- ✅ 搜索索引

无需手动操作！

### 3. 检查数据状态

```bash
make check-data
```

这将显示数据库中所有数据的统计信息。

## 手动初始化产品数据

如果自动初始化失败或需要重新加载数据，可以使用以下命令：

### 初始化所有产品数据

```bash
make init-products
```

此命令会执行以下操作：

1. **加载子产品数据** - `fixtures/child_products.json`
2. **导入CSV产品数据** - `fixtures/*.csv`（所有CSV文件）
3. **导入产品图片** - `fixtures/images.tar.gz`
4. **加载国家数据** - 用于地址选择
5. **加载页面数据** - CMS页面
6. **加载分类和优惠数据** - 产品分类、优惠活动
7. **重建搜索索引** - Haystack搜索索引

### 单独执行各项操作

```bash
# 进入容器
make shell

# 在容器内执行
cd /app/sandbox

# 加载子产品
python manage.py loaddata fixtures/child_products.json

# 导入CSV产品数据
python manage.py oscar_import_catalogue fixtures/books.essential.csv
python manage.py oscar_import_catalogue fixtures/books.computers-in-fiction.csv
python manage.py oscar_import_catalogue fixtures/books.hacking.csv

# 导入产品图片
python manage.py oscar_import_catalogue_images fixtures/images.tar.gz

# 加载国家数据
python manage.py oscar_populate_countries --initial-only

# 加载其他数据
python manage.py loaddata fixtures/pages.json
python manage.py loaddata fixtures/ranges.json
python manage.py loaddata fixtures/offers.json
python manage.py loaddata fixtures/orders.json

# 重建搜索索引
python manage.py clear_index --noinput
python manage.py update_index catalogue

# 退出容器
exit
```

## 数据管理命令

### 查看数据统计

```bash
make check-data
```

```bash
make check-data
```

显示内容：
- 用户统计（总用户数、管理员数）
- 产品统计（总产品、父产品、子产品）
- 分类统计（分类数、产品分类关联）
- 图片统计（产品图片数）
- 库存统计（库存记录数）
- 合作伙伴统计
- 优惠统计（优惠数量、优惠范围）
- 订单统计

### 图片管理

**查看缺失图片的产品**：
```bash
make check-images
```

**按分类查看图片覆盖情况**：
```bash
make check-images-detail
```

**为缺失图片的产品添加占位图**：

预览模式（不实际添加）：
```bash
make add-placeholder-images
```

为前10个缺失图片的产品添加：
```bash
make add-placeholder-images-10
```

为所有缺失图片的产品添加：
```bash
make add-all-placeholder-images
```

**在管理后台手动添加图片**：
1. 访问：http://localhost:8080/admin/catalogue/product/
2. 选择没有图片的产品
3. 编辑产品，在 Images 区域上传图片

### 重建搜索索引

```bash
make rebuild-index
```

用于修复 `/catalogue/` 页面的搜索错误。

### 重置所有数据（危险操作）

```bash
make reset-data
```

⚠️ **警告**：此操作会删除所有数据并重新加载！

## 快捷命令总结

| 命令 | 说明 |
|------|------|
| `make up` | 启动服务（PostgreSQL） |
| `make up-sqlite` | 启动服务（SQLite） |
| `make check-data` | 查看数据统计 |
| `make init-products` | 初始化产品数据 |
| `make check-images` | 检查缺失图片的产品 |
| `make check-images-detail` | 按分类查看图片覆盖情况 |
| `make add-placeholder-images` | 预览占位图添加 |
| `make add-placeholder-images-10` | 为前10个产品添加占位图 |
| `make rebuild-index` | 重建搜索索引 |
| `make update-index` | 增量更新搜索索引 |

| `make quick-admin` | 快速创建管理员 |
| `make list-admins` | 列出所有管理员 |
| `make reset-data` | 重置所有数据 |
| `make shell` | 进入容器 |
| `make logs` | 查看日志 |
| `make down` | 停止服务 |

## 默认数据

### 用户数据

通过 `fixtures/auth.json` 加载：

1. **superuser** - 超级管理员
   - 用户名：`superuser`
   - 邮箱：`superuser@example.com`
   - 权限：超级用户、员工

2. **staff** - 普通管理员
   - 用户名：`staff`
   - 邮箱：`staff@example.com`
   - 权限：员工、非超级用户

⚠️ **注意**：这些用户的密码已哈希，如需创建新管理员请使用：
```bash
make quick-admin
# 或
make create-admin USER=<用户名> PASS=<密码>
```

### 产品数据

示例产品包括：
- 必读书籍
- 计算机小说
- 黑客技术书籍

产品结构：
- 父产品（Product Class）：定义产品类别
- 子产品（Product）：具体产品，包含库存信息

### 分类数据

产品分类通过 `fixtures/ranges.json` 加载。

### 优惠数据

优惠活动通过 `fixtures/offers.json` 加载。

## 故障排查

### 产品未显示

1. 检查数据是否加载：
   ```bash
   make check-data
   ```

2. 如果产品数为0，手动初始化：
   ```bash
   make init-products
   ```

3. 重建搜索索引：
   ```bash
   make rebuild-index
   ```

### 搜索页面报错

错误：`AttributeError: 'NoneType' object has no attribute 'facet_counts'`

解决：
```bash
make rebuild-index
```

### 图片未显示

1. 检查图片是否导入：
   ```bash
   make check-data
   ```

2. 检查媒体文件权限：
   ```bash
   make shell
   ls -la /app/sandbox/public/media/
   exit
   ```

### 数据导入失败

1. 确认 fixtures 文件存在：
   ```bash
   make shell
   ls -la /app/sandbox/fixtures/
   exit
   ```

2. 手动执行单个命令查看详细错误：
   ```bash
   make shell
   cd /app/sandbox
   python manage.py loaddata fixtures/child_products.json
   ```

## 最佳实践

### 开发环境

1. 使用 SQLite 快速启动：
   ```bash
   make up-sqlite
   ```

2. 数据损坏时快速重置：
   ```bash
   make reset-data
   ```

### 生产环境

1. 使用 PostgreSQL：
   ```bash
   make up
   ```

2. 定期备份数据：
   ```bash
   # 备份数据库
   docker-compose exec db pg_dump -U oscar_user oscar_db > backup.sql
   ```

3. 修改默认密码：
   ```bash
   # 创建新的管理员
   make create-admin USER=myadmin PASS=StrongPassword123
   ```

## 附录：初始化脚本说明

### init-db.sh

容器启动时自动执行，负责：
1. 运行数据库迁移
2. 检查是否已初始化
3. 首次启动时加载所有数据
4. 启动 uWSGI 服务

### init_products.sh

专门用于产品数据初始化：
1. 加载子产品数据
2. 导入CSV格式产品数据
3. 导入产品图片
4. 加载国家数据
5. 加载页面数据
6. 加载分类和优惠数据
7. 重建搜索索引

### check_data.py

数据统计脚本，显示所有数据的统计信息。

### quick_admin.py

快速创建管理员脚本：
- 支持非交互式创建
- 支持环境变量配置
- 可更新已存在用户的密码

---

**更新时间**：2025-12-30
