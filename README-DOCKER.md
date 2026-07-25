# Django Oscar Docker Compose 部署指南

## 概述

本项目使用 Docker Compose 部署 Django Oscar 电子商务平台，无需修改 django-oscar 源码。

### 项目结构

```
e-commerce/python/django-oscar-research/
├── django-oscar/              # django-oscar 官方源码（不修改）
│   ├── sandbox/               # 示例应用
│   └── src/                   # oscar 核心代码
├── Dockerfile                 # 自定义 Dockerfile（基于 python:3.12 扩展：装 Node.js、oscar、uwsgi）
├── docker-compose.yml         # Docker Compose 配置 (PostgreSQL)
├── docker-compose.sqlite.yml  # Docker Compose 配置 (SQLite)
├── .env                       # 环境变量配置
├── .dockerignore             # Docker 忽略文件
├── init-db.sh                # 自动初始化脚本（迁移+示例数据+collectstatic）
├── Makefile                  # 便捷命令
└── README-DOCKER.md          # 本文档
```

### 特点

- ✅ 不修改 django-oscar 源码
- ✅ 支持自动初始化数据库和示例数据
- ✅ 提供 PostgreSQL 和 SQLite 两种配置
- ✅ 使用自定义 Dockerfile（基于官方 python:3.12 镜像扩展）
- ✅ 数据持久化
- ✅ 提供 Makefile 便捷命令

## 前置要求

- Docker 20.10+
- Docker Compose 2.0+

## 快速开始

### 方式一：使用 Makefile（推荐）

```bash
# 查看所有可用命令
make help

# 启动服务（PostgreSQL 版本）
make up

# 或使用 SQLite 版本（无需数据库容器）
make up-sqlite
```

启动后访问 http://localhost:8080 即可使用。

### 方式二：使用 Docker Compose

```bash
# PostgreSQL 版本
docker compose up -d

# SQLite 版本
docker compose -f docker-compose.sqlite.yml up -d

# 查看日志
docker compose logs -f web
```

### 自动初始化

本项目已配置自动初始化脚本，首次启动时会自动：
- 运行数据库迁移
- 加载示例数据（商品、用户、订单等）
- 收集静态文件
- 建立搜索索引

无需手动执行初始化命令。

### 手动初始化（可选）

如需重新初始化或手动操作：

```bash
# 进入 web 容器
docker compose exec web bash

# 在容器内执行以下命令
cd /app/sandbox

# 运行数据库迁移
python manage.py migrate

# 加载用户数据
python manage.py loaddata fixtures/auth.json

# 加载示例商品数据
python manage.py loaddata fixtures/child_products.json
python manage.py oscar_import_catalogue fixtures/*.csv

# 导入图片
python manage.py oscar_import_catalogue_images fixtures/images.tar.gz

# 加载国家数据
python manage.py oscar_populate_countries --initial-only

# 加载页面、分类和优惠数据
python manage.py loaddata fixtures/pages.json fixtures/ranges.json fixtures/offers.json

# 加载订单示例数据
python manage.py loaddata fixtures/orders.json

# 重建搜索索引
python manage.py clear_index --noinput
python manage.py update_index catalogue

# 清理缩略图缓存
python manage.py thumbnail cleanup

# 收集静态文件
python manage.py collectstatic --noinput

# 退出容器
exit
```

### 3. 访问应用

打开浏览器访问：http://localhost:8080

## 服务说明

### db (PostgreSQL)
- 镜像：postgres:15-alpine
- 数据库名：oscar_db
- 用户：oscar_user
- 密码：oscar_password

### web (Django Oscar)
- 基于官方 python:3.12 镜像扩展的自定义 Dockerfile
- 使用 uWSGI 运行
- 监听端口：容器内部 8080；宿主机对外端口由 `WEB_PORT`（默认 8080）控制。
- 自动连接 PostgreSQL 数据库

> ⚠️ **端口冲突**：若宿主机 8080 已被占用，`make up` 会报
> `bind: address already in use`。在 `.env` 里加一行 `WEB_PORT=8092`（或任意空闲端口），
> 重新 `make up` 即可，访问地址相应改为 `http://<host>:8092/`。

## 环境变量配置

可以通过 `.env` 文件或 `docker-compose.yml` 修改环境变量：

- `DEBUG`: 调试模式（生产环境设为 False）
- `SECRET_KEY`: Django 密钥（生产环境必须修改）
- `ALLOWED_HOSTS`: 允许的主机列表
- `DATABASE_ENGINE`: 数据库引擎
- `DATABASE_NAME`: 数据库名称
- `DATABASE_USER`: 数据库用户
- `DATABASE_PASSWORD`: 数据库密码
- `DATABASE_HOST`: 数据库主机
- `DATABASE_PORT`: 数据库端口

## 常用命令

### 使用 Makefile（推荐）

```bash
# 查看所有命令
make help

# 启动服务
make up                    # PostgreSQL 版本
make up-sqlite             # SQLite 版本

# 停止服务
make down                  # PostgreSQL 版本
make down-sqlite           # SQLite 版本

# 重启服务
make restart               # PostgreSQL 版本
make restart-sqlite        # SQLite 版本

# 查看日志
make logs                  # 所有服务
make logs-web              # 仅 web 服务
make logs-db               # 仅 db 服务

# 构建镜像
make build                 # PostgreSQL 版本
make build-sqlite          # SQLite 版本

# 进入容器
make shell                 # 进入 web 容器
make shell-sqlite          # 进入 web 容器 (SQLite)

# 进入数据库
make db-shell              # 进入 PostgreSQL

# Django 管理命令
make createsuperuser       # 创建超级用户
make collectstatic         # 收集静态文件
make migrate               # 运行迁移

# 清理
make clean                 # 清理容器和数据卷 (PostgreSQL)
make clean-sqlite          # 清理容器和数据卷 (SQLite)

# 查看状态
make status                # 查看服务状态 (PostgreSQL)
make status-sqlite         # 查看服务状态 (SQLite)
```

### 使用 Docker Compose

#### 启动服务
```bash
docker compose up -d
```

#### 停止服务
```bash
docker compose down
```

#### 停止并删除数据卷
```bash
docker compose down -v
```

#### 查看日志
```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f web
docker compose logs -f db
```

#### 重新构建镜像
```bash
docker compose build
```

#### 执行 Django 命令
```bash
# 进入容器
docker compose exec web bash

# 执行迁移
docker compose exec web python /app/sandbox/manage.py migrate

# 创建超级用户
docker compose exec web python /app/sandbox/manage.py createsuperuser
```

#### 查看运行状态
```bash
docker compose ps
```

## 使用 SQLite 替代 PostgreSQL

项目提供了两种数据库配置：

### PostgreSQL（推荐用于生产环境）
```bash
make up
```
需要 PostgreSQL 容器，适合多实例和并发访问。

### SQLite（适合开发环境）
```bash
make up-sqlite
```
无需额外数据库容器，更轻量，适合单机开发。

两种配置完全兼容，数据持久化方式：
- PostgreSQL：使用 `postgres_data` volume
- SQLite：使用 `sqlite_data` volume，数据库文件位于 `/app/sandbox/db.sqlite`

## 数据持久化

- PostgreSQL 数据存储在 `postgres_data` volume 中
- 媒体文件存储在 `media_volume` volume 中

## 生产环境部署

生产环境需要：

1. 修改 `SECRET_KEY` 为强随机密钥
2. 设置 `DEBUG=False`
3. 配置正确的 `ALLOWED_HOSTS`
4. 使用 HTTPS
5. 配置适当的 `CACHES` 设置
6. 设置邮件后端
7. 配置适当的日志级别

## 故障排查

### 数据库连接失败
- 检查 db 服务是否正常运行：`docker compose ps db`
- 查看数据库日志：`docker compose logs db`
- 确认数据库健康检查通过

### 静态文件 404
- 重新收集静态文件：`docker compose exec web python /app/sandbox/manage.py collectstatic --noinput`

### 无法访问应用
- 检查端口是否被占用：`lsof -i :8080`
- 确认服务正常运行：`docker compose ps`
- 查看服务日志：`docker compose logs web`

## 备注

- 本配置不修改 django-oscar 源码
- 使用自定义 Dockerfile（基于官方 python:3.12 镜像扩展） 构建 web 服务
- 支持通过环境变量灵活配置
- 数据持久化使用 Docker volumes
- 自动初始化脚本会在首次启动时执行

## 快速参考

### 三步启动

```bash
# 1. 进入项目目录
cd e-commerce/python/django-oscar-research

# 2. 启动服务（PostgreSQL 或 SQLite）
make up           # 或 make up-sqlite

# 3. 访问应用
# 打开浏览器 http://localhost:8080
```

### 默认凭证

- **超级用户**：需要手动创建 `make createsuperuser`
- **示例数据**：自动加载，无需额外配置
- **数据库**：
  - PostgreSQL: `oscar_user/oscar_password@oscar_db`
  - SQLite: 文件位于 `/app/sandbox/db.sqlite`

### 常见任务

| 任务 | 命令 |
|------|------|
| 查看日志 | `make logs` |
| 进入容器 | `make shell` |
| 创建超级用户 | `make createsuperuser` |
| 运行迁移 | `make migrate` |
| 收集静态文件 | `make collectstatic` |
| 停止服务 | `make down` |
| 完全清理 | `make clean` |
