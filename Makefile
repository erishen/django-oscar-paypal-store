# Detect docker compose command: prefer the legacy V1 binary (docker-compose),
# fall back to the V2 plugin (docker compose) which is what modern Docker
# installs ship with. This keeps the Makefile working on both old and new hosts.
COMPOSE := $(shell command -v docker-compose >/dev/null 2>&1 && echo docker-compose || echo "docker compose")

.PHONY: help up down restart logs build shell db-shell init clean status

help: ## 显示帮助信息
	@echo "Django Oscar Docker 管理命令"
	@echo ""
	@echo "使用方法: make <target>"
	@echo ""
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "更多帮助: cat README.md"
	@echo ""

up: ## 启动服务 (PostgreSQL)
	$(COMPOSE) up -d
	@echo ""
	@echo "==================================="
	@echo "服务已启动!"
	@echo "访问地址: http://localhost:8080"
	@echo "==================================="
	@echo ""
	@echo "查看日志: make logs"
	@echo "停止服务: make down"
	@echo ""

up-sqlite: ## 启动服务 (SQLite)
	$(COMPOSE) -f docker-compose.sqlite.yml up -d
	@echo ""
	@echo "==================================="
	@echo "服务已启动 (SQLite)!"
	@echo "访问地址: http://localhost:8080"
	@echo "==================================="
	@echo ""
	@echo "查看日志: make logs"
	@echo "停止服务: make down-sqlite"
	@echo ""

down: ## 停止并删除容器
	$(COMPOSE) down
	@echo "服务已停止"

down-sqlite: ## 停止并删除容器 (SQLite)
	$(COMPOSE) -f docker-compose.sqlite.yml down
	@echo "服务已停止"

restart: ## 重启服务
	$(COMPOSE) restart
	@echo "服务已重启"

restart-sqlite: ## 重启服务 (SQLite)
	$(COMPOSE) -f docker-compose.sqlite.yml restart
	@echo "服务已重启"

logs: ## 查看日志
	$(COMPOSE) logs -f

logs-web: ## 查看 web 服务日志
	$(COMPOSE) logs -f web

logs-db: ## 查看 db 服务日志
	$(COMPOSE) logs -f db

build: ## 构建镜像
	$(COMPOSE) build --no-cache

build-sqlite: ## 构建镜像 (SQLite)
	$(COMPOSE) -f docker-compose.sqlite.yml build --no-cache

shell: ## 进入 web 容器
	$(COMPOSE) exec web bash

shell-sqlite: ## 进入 web 容器 (SQLite)
	$(COMPOSE) -f docker-compose.sqlite.yml exec web bash

db-shell: ## 进入数据库容器
	$(COMPOSE) exec db psql -U oscar_user -d oscar_db

createsuperuser: ## 创建超级用户 (交互式)
	$(COMPOSE) exec web python /app/sandbox/manage.py createsuperuser

quick-admin: ## 快速创建管理员 (默认: admin/admin123456)
	$(COMPOSE) exec web python /app/scripts/1-quick_admin.py

create-admin: ## 创建自定义管理员
	@if [ -z "$(USER)" ]; then \
		echo "用法: make create-admin USER=<用户名> PASS=<密码> [EMAIL=<邮箱>]"; \
		exit 1; \
	fi
	$(COMPOSE) exec web python /app/scripts/1-quick_admin.py $(USER) $(PASS) $(EMAIL)

list-admins: ## 列出所有管理员
	$(COMPOSE) exec web python /app/scripts/1-quick_admin.py --list-only || \
	$(COMPOSE) exec web python /app/sandbox/manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); admins = User.objects.filter(is_staff=True); print('=== 管理员列表 ==='); [print(f'- {u.username}: {u.email} ({\"超级用户\" if u.is_superuser else \"普通管理员\"})') for u in admins]; print(f'总计: {admins.count()} 个管理员')" 2>/dev/null || echo "请先确保服务运行: make up"

collectstatic: ## 重新收集静态文件
	$(COMPOSE) exec web python /app/sandbox/manage.py collectstatic --noinput

migrate: ## 运行数据库迁移
	$(COMPOSE) exec web python /app/sandbox/manage.py migrate --noinput

rebuild-index: ## 重建搜索索引
	$(COMPOSE) exec web python /app/scripts/6-manage_search_index.py --rebuild

update-index: ## 增量更新搜索索引
	$(COMPOSE) exec web python /app/scripts/6-manage_search_index.py --update

init-products: ## 初始化产品数据
	$(COMPOSE) exec web bash /app/scripts/2-init_products.sh
	@echo ""
	@echo "产品数据初始化完成!"
	@echo "查看统计: make check-data"

check-data: ## 查看数据统计
	$(COMPOSE) exec web python /app/scripts/3-check_data.py

check-images: ## 检查缺失图片的产品
	$(COMPOSE) exec web python /app/scripts/4-check_missing_images.py

check-images-detail: ## 检查缺失图片的产品（按分类）
	$(COMPOSE) exec web python /app/scripts/4-check_missing_images.py --category

add-placeholder-images: ## 为缺失图片的产品添加占位图（预览模式）
	$(COMPOSE) exec web python /app/scripts/5-add_default_images.py --dry-run

add-placeholder-images-10: ## 为前10个缺失图片的产品添加占位图
	$(COMPOSE) exec web python /app/scripts/5-add_default_images.py --limit 10

add-all-placeholder-images: ## 为所有缺失图片的产品添加占位图
	@echo "⚠️  此操作将为所有缺失图片的产品添加占位图"
	@$(COMPOSE) exec web python /app/scripts/5-add_default_images.py <<< "yes" || true

reset-data: ## 重置所有数据（危险操作）
	@echo "⚠️  警告：此操作将删除所有数据!"
	@read -p "确定要继续吗？(yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(COMPOSE) exec web python /app/sandbox/manage.py flush --noinput; \
		make init-products; \
	else \
		echo "操作已取消"; \
	fi

clean: ## 清理所有容器和数据
	$(COMPOSE) down -v
	@echo "已清理所有容器和数据卷"

clean-sqlite: ## 清理所有容器和数据 (SQLite)
	$(COMPOSE) -f docker-compose.sqlite.yml down -v
	@echo "已清理所有容器和数据卷"

status: ## 查看服务状态
	$(COMPOSE) ps

status-sqlite: ## 查看服务状态 (SQLite)
	$(COMPOSE) -f docker-compose.sqlite.yml ps
