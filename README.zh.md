# oscar-paypal-store

一个基于 [Django Oscar](https://github.com/django-oscar/django-oscar)（4.1）的电子商务沙箱，集成了 **PayPal Express Checkout**、**简体中文（zh-CN）本地化** 与一个 **演示版店铺 UI**。

> ⚠️ **这是一个技术演示 / 作品集项目，不是生产店铺。**
> PayPal 仅运行在 **沙箱模式**（`PAYPAL_MODE=sandbox`）。请勿切换到 live，也不要用它接收真实付款。详见 [安全说明](#安全说明)。

---

## 项目包含什么

- **Django Oscar 4.1** 前台（商品目录、购物篮、结账、后台）基于 Django 5.2 + Bootstrap 4。
- **PayPal Express Checkout** 集成（OAuth → 创建订单 → 批准 → 捕获 → 退款），对接 PayPal 沙箱 API。
- **幂等支付** —— `create_order` 每次点击使用唯一幂等键；`capture_order` 可安全重试（GET 对账 + 稳定的 `PayPal-Request-Id` + 把 `ORDER_ALREADY_CAPTURED` 视为成功）。
- **后台退款直通 PayPal** —— Oscar 后台的「退款」操作通过 facade 执行**真实**的 PayPal 退款，而不只是本地记账。
- **zh-CN 本地化** —— 项目级 `django.po` 提供约 83 个高频 UI 词条翻译；语言切换器为 **EN | 中文** 双按钮。
- **演示 UI** —— 现代化电商主题 + 固定显示的 **「演示站点 · DEMO」** 角标，明确标识为非商业演示。
- **一键 Docker** —— `docker compose up` 拉起 web（uWSGI）+ PostgreSQL 服务，自动迁移并灌入示例数据。

## 技术栈

| 层 | 选型 |
|----|------|
| 语言 | Python 3.12 |
| 框架 | Django Oscar 4.1 / Django 5.2 |
| Web 服务器 | uWSGI（端口 8080） |
| 数据库 | PostgreSQL 15（Alpine） |
| 搜索引擎 | Haystack + Whoosh |
| 前端构建 | Node.js 20（npm） |
| 编排 | Docker Compose |

> Compose 内部**项目名被固定**为 `django-oscar-research`（`docker-compose.yml` 中的 `name:`）。
> 因此重命名目录**不会**破坏正在运行的容器、数据卷或已固化进镜像的定制代码。

## 前置要求

- Docker 20.10+ 与 Docker Compose v2
- 一个 PayPal 开发者账号，用于获取**沙箱**凭据（见 [PayPal 配置](#paypal-沙箱配置)）
- `git`（用于克隆）

## 快速开始

```bash
# 1. 克隆
git clone git@github.com:erishen/oscar-paypal-store.git
cd oscar-paypal-store

# 2. 创建环境文件（必须 —— 见下方说明）
cp .env.example .env
#    然后编辑 .env，填入 SECRET_KEY、DATABASE_PASSWORD，
#    以及你的 PayPal 沙箱 CLIENT_ID / CLIENT_SECRET。

# 3. 构建并启动（重新构建镜像，把所有定制烤入）
docker compose up -d --build

# 4. 打开店铺
#    中文： http://localhost:8080/zh-cn/
#    英文： http://localhost:8080/en-gb/
```

> 🔴 **`.env` 是必填项，且不在仓库中**（已被 gitignore）。
> `docker-compose.yml` 通过 `${DATABASE_PASSWORD:?...}` 读取 `DATABASE_PASSWORD`，
> 因此没有 `.env` 直接启动会立即失败。请务必先 `cp .env.example .env`，
> 并至少填入 `SECRET_KEY` 与 `DATABASE_PASSWORD`。

### 创建管理员 / 超级用户

```bash
make quick-admin          # 创建 admin / admin123456
# 或
make createsuperuser      # 交互式创建
```

随后访问带语言前缀的后台，例如
`http://localhost:8080/zh-cn/dashboard/`（或 `/en-gb/dashboard/`）。
Django 管理后台位于 `/zh-cn/admin/`（或 `/en-gb/admin/`）。

## 环境变量

所有变量都写在 `.env` 中（从 `.env.example` 复制）。主要项：

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEBUG` | 否 | 本沙箱为 `True`。生产环境设 `False`。 |
| `SECRET_KEY` | **是** | 使用强随机值。 |
| `DATABASE_ENGINE` | 否 | `django.db.backends.postgresql_psycopg2`（默认）。 |
| `DATABASE_NAME` | 否 | `oscar_db`（默认）。 |
| `DATABASE_USER` | 否 | `oscar_user`（默认）。 |
| `DATABASE_PASSWORD` | **是** | 由 Compose 读取；首次初始化时数据库用户密码会更新为一致。 |
| `PAYPAL_CLIENT_ID` | **是\*** | 沙箱客户端 ID。`*` 仅结账时需要。 |
| `PAYPAL_CLIENT_SECRET` | **是\*** | 沙箱客户端密钥。 |
| `PAYPAL_MODE` | 否 | `sandbox`（默认）。保持沙箱。 |

PayPal 凭据**绝不入库**（`.env` 已被 gitignore），也从未进入过 git 历史。

## PayPal 沙箱配置

1. 在 <https://developer.paypal.com/dashboard/applications/sandbox> 创建一个应用。
2. 把 **Client ID** 与 **Secret** 填入 `.env` 的 `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET`。
3. 保持 `PAYPAL_MODE=sandbox`。
4. 在前台把商品加入购物篮 → 结账 → *Pay with PayPal* → 用 PayPal **沙箱买家**账号登录 → 批准 → 跳转回站点并生成 Oscar 订单。退款可在 Oscar 后台发起。

支付流程实现位于 `django-oscar/sandbox/apps/paypal_express/`（fork 的 Oscar sandbox 应用），HTTP facade 在 `facade.py`。

## 国际化（en-gb / zh-cn）

在 `settings.LANGUAGES` 中注册的可选语言只有 **`en-gb`** 和 **`zh-cn`**。

- 前台 URL 带有语言前缀：`/zh-cn/...` 与 `/en-gb/...`。
- 👉 **没有 `/en-us/` 前缀** —— 访问 `/en-us/` 会按设计返回 404（英文语言码是 `en-gb`）。英文请用 `/en-gb/`。
- zh-CN 界面文案由 `django-oscar/sandbox/locale/zh_CN/LC_MESSAGES/django.po` 提供（项目 `LOCALE_PATHS` 优先级高于库内翻译）。
- 顶部切换器是 **EN | 中文** 双按钮，向 Django `set_language` 提交时使用「去语言前缀」的 `next`（因此切换语言时不会卡在旧前缀上）。

## 项目结构

```
oscar-paypal-store/
├── django-oscar/                 # Vendored Django Oscar 源码 + sandbox（已定制）
│   └── sandbox/
│       ├── apps/
│       │   ├── paypal_express/   # PayPal facade + 视图（幂等捕获/退款）
│       │   └── dashboard/        # fork 的后台，退款直通真实 PayPal
│       ├── locale/zh_CN/         # 简体中文翻译
│       ├── templates/oscar/      # base / nav / product 模板覆盖
│       └── static/oscar/css/     # 演示主题（custom.css）+ DEMO 角标
├── docker-compose.yml            # 固定项目名：django-oscar-research
├── Dockerfile                   # python:3.12 + Node 20 + uWSGI
├── init-db.sh                   # 迁移 + 灌数据（有数据则跳过）+ 建索引
├── scripts/                     # 辅助管理命令
├── .env.example                 # 必填环境变量模板
├── UPSTREAM.md                  # 上游基线 + 定制清单
├── README.md / README.zh.md     # 文档
└── PRODUCT-DATA-GUIDE.md        # 商品数据指南
```

## 数据与灌库

首次启动时，`init-db.sh` 会执行迁移、加载夹具（用户、商品目录、图片、国家、页面、范围、优惠、订单）、建立搜索索引并收集静态文件。**如果数据已存在则跳过**，因此重启不会重复灌入种子数据。

当前种子状态：**约 140 个商品**（无图商品已删除）与 **4 笔示例订单**。数据持久化在 `postgres_data` 数据卷中。

## 代码改动后重新构建

Docker 镜像由本地 `django-oscar/` 源码构建，因此对 vendored Oscar sandbox 的任何改动（PayPal facade、模板、CSS、翻译……）都必须**烤进镜像**才能在容器重建后保留：

```bash
docker compose build web
docker compose up -d
```

`make build` / `make up` 作用相同。运行期间用 `docker cp` 热补可以生效，但容器重建后会丢失 —— 持久改动请优先重新构建镜像。

## Makefile 速查

| 命令 | 用途 |
|------|------|
| `make up` / `make down` | 启动 / 停止（PostgreSQL） |
| `make up-sqlite` | 用 SQLite 代替 PostgreSQL 启动 |
| `make build` | 构建 web 镜像 |
| `make restart` | 重启服务 |
| `make logs` / `make logs-web` | 查看日志 |
| `make shell` | 进入 web 容器 |
| `make db-shell` | 进入 PostgreSQL |
| `make quick-admin` | 创建 `admin`/`admin123456` |
| `make migrate` | 执行迁移 |
| `make rebuild-index` | 重建搜索索引 |
| `make check-data` | 显示商品 / 订单数量 |
| `make clean` | 停止**并删除**容器 + 数据卷 |

## 已知问题 / 常见问题

- **`/en-us/` 返回 404** —— 这是预期行为。英文语言码是 `en-gb`，请用 `/en-gb/`。
- **`docker compose up` 前必须先创建 `.env`** —— `DATABASE_PASSWORD` 为必填。
- **仅沙箱** —— PayPal 对接的是沙箱 API；这是演示，不是店铺。
- **`settings.py` 有一个硬编码的兜底 `SECRET_KEY`**（低风险），真实值来自 `.env`。任何真实部署都应覆盖它。
- 种子商品目录是上游 Oscar 的示例数据；无图商品已删除，使前台更整洁。

## 安全说明

- `.env`（含 `SECRET_KEY`、`DATABASE_PASSWORD`、PayPal 凭据）**已被 gitignore**，**从未提交**入库。
- `DATABASE_PASSWORD` 通过 `.env` 提供给容器（`POSTGRES_PASSWORD: ${DATABASE_PASSWORD:?...}`），**未**硬编码在 `docker-compose.yml` 中。
- PayPal 运行在**沙箱**模式。接收真实付款需要支付牌照 / 合规接入（例如国内的 EDI）以及不同的支付底座 —— 不在本演示范围内。
- 生产环境还需额外设置 `DEBUG=False`、配置 `ALLOWED_HOSTS`、在反向代理处终止 TLS，并备份数据库卷。

## 许可证

Django Oscar 基于 **BSD-3-Clause** 许可证发布。本沙箱及其定制代码按「原样」提供，仅用于演示目的。
