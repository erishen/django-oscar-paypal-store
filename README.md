# Django Oscar Docker 部署

基于 Docker Compose 的 Django Oscar 电子商务平台快速部署方案。

## 快速开始

### 1. 启动服务

```bash
# PostgreSQL 版本（推荐）
make up

# SQLite 版本（开发环境）
make up-sqlite
```

### 2. 访问应用

- **首页**: http://localhost:8080/zh-cn/
- **管理后台**: http://localhost:8080/admin/
- **产品目录**: http://localhost:8080/zh-cn/catalogue/

### 3. 创建管理员

```bash
# 快速创建管理员（默认：admin/admin123456）
make quick-admin

# 或自定义创建
make create-admin USER=<用户名> PASS=<密码>
```

## 常用命令

### 服务管理

| 命令 | 说明 |
|------|------|
| `make up` | 启动服务（PostgreSQL） |
| `make up-sqlite` | 启动服务（SQLite） |
| `make down` | 停止服务 |
| `make restart` | 重启服务 |
| `make logs` | 查看日志 |
| `make status` | 查看服务状态 |

### 数据管理

| 命令 | 说明 |
|------|------|
| `make check-data` | 查看数据统计 |
| `make check-images` | 检查缺失图片的产品 |
| `make init-products` | 初始化产品数据 |
| `make rebuild-index` | 重建搜索索引 |
| `make update-index` | 增量更新搜索索引 |

| `make reset-data` | 重置所有数据 |

### 图片管理

| 命令 | 说明 |
|------|------|
| `make add-placeholder-images` | 预览占位图添加 |
| `make add-placeholder-images-10` | 为前10个产品添加占位图 |
| `make add-all-placeholder-images` | 为所有缺失图片的产品添加占位图 |

### 容器操作

| 命令 | 说明 |
|------|------|
| `make shell` | 进入 web 容器 |
| `make db-shell` | 进入 PostgreSQL 数据库 |
| `make migrate` | 运行数据库迁移 |
| `make collectstatic` | 收集静态文件 |

## 项目结构

```
django-oscar-research/
├── django-oscar/                 # Django Oscar 源码
├── docker-compose.yml            # PostgreSQL 配置
├── docker-compose.sqlite.yml     # SQLite 配置
├── Dockerfile                   # Docker 镜像构建
├── Makefile                    # 便捷命令
├── init-db.sh                  # 容器启动初始化脚本
├── scripts/                    # 辅助脚本目录
│   ├── quick_admin.py           # 快速创建管理员
│   ├── check_data.py            # 数据统计
│   ├── check_missing_images.py  # 检查图片
│   ├── add_default_images.py     # 添加占位图
│   ├── manage_search_index.py    # 搜索索引管理
│   ├── init_products.sh        # 产品数据初始化
│   └── README.md              # 脚本文档
├── README.md                   # 项目主文档
├── README-DOCKER.md          # Docker 部署详细文档
└── PRODUCT-DATA-GUIDE.md     # 产品数据管理指南
```

## 数据状态

- ✅ 总产品数：209 个
- ✅ 产品图片：209 张（100% 覆盖）
- ✅ 搜索索引：已建立
- ✅ 示例数据：已加载

## 数据库配置

### PostgreSQL（生产环境推荐）

- 数据库：`oscar_db`
- 用户：`oscar_user`
- 密码：`oscar_password`
- 持久化：`postgres_data` volume

### SQLite（开发环境）

- 数据库文件：`/app/sandbox/db.sqlite`
- 持久化：`sqlite_data` volume

## 默认账号

### 管理员

使用 `make quick-admin` 创建或使用管理后台手动创建。

### 示例用户

fixtures 中包含示例用户（`fixtures/auth.json`），但密码已哈希，建议创建新账号。

## 技术栈

- **Python**: 3.12
- **Django**: 通过 django-oscar
- **数据库**: PostgreSQL 15 / SQLite
- **Web 服务器**: uWSGI
- **搜索引擎**: Haystack + Whoosh
- **容器平台**: Docker Compose + OrbStack

## 文档

详细文档请参考：

- **Docker 部署**: [README-DOCKER.md](README-DOCKER.md)
- **产品数据管理**: [PRODUCT-DATA-GUIDE.md](PRODUCT-DATA-GUIDE.md)

## 故障排查

### 数据库连接失败
```bash
make logs-db
```

### 产品未显示
```bash
make check-data
make rebuild-index    # 重建搜索索引
make update-index     # 增量更新索引
```

### 图片问题
```bash
make check-images
```

### 完全重置
```bash
make clean
make up
```

## 生产环境部署

1. 修改 `.env` 文件
   - `SECRET_KEY`：使用强随机密钥
   - `DEBUG=False`
   - `ALLOWED_HOSTS`：设置正确的域名

2. 使用 PostgreSQL
   ```bash
   make up
   ```

3. 配置 HTTPS（推荐使用 Nginx 反向代理）

4. 定期备份数据
   ```bash
   docker-compose exec db pg_dump -U oscar_user oscar_db > backup.sql
   ```

## 许可证

Django Oscar 使用 BSD-3-Clause 许可证。
