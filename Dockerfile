FROM python:3.12
ARG BUILD_DATE
ENV PYTHONUNBUFFERED=1
ENV BUILD_DATE=${BUILD_DATE:-unknown}

# Use a China-accessible PyPI mirror with longer timeout + retries so the
# image builds on restricted networks (files.pythonhosted.org times out otherwise).
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_TIMEOUT=120
ENV PIP_RETRIES=5
ENV PIP_NO_CACHE_DIR=1
# Use a China-accessible npm mirror for the frontend asset build step.
ENV npm_config_registry=https://registry.npmmirror.com

# Install Node.js from nodesource (includes npm automatically) and curl for healthcheck
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && \
    apt-get install -y nodejs curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Note: django-oscar 使用 pyproject.toml 打包（无 requirements.txt）。
# Python 依赖在下方通过 `pip install -e .[test]` 安装（含 DB 驱动/搜索/缩略图等）。

# Create user
RUN groupadd -r django && useradd -r -g django django

# Copy source code
COPY django-oscar /app
RUN chown -R django:django /app

# Ensure media/static dirs exist with django ownership. `public/media` is a
# named volume at runtime; Docker copies this dir's ownership on first mount,
# so chowning here makes the volume writable by the django user (otherwise
# `oscar_import_catalogue_images` and `collectstatic` fail with PermissionError).
RUN mkdir -p /app/sandbox/public/media/images /app/sandbox/public/static && \
    chown -R django:django /app/sandbox/public

# Copy helper scripts
COPY scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh && \
    chown -R django:django /app/scripts/

WORKDIR /app

# Install Oscar (editable) with test extras: DB driver, search backend, thumbnails, etc.
RUN pip install --no-cache-dir -e .[test]

# Pin django-treebeard to 4.5.x. Oscar 4.1 calls `Category.get_tree()` as a
# model classmethod; treebeard >=4.6 moved `get_tree` onto the manager and
# replaced the model method with a deprecation shim that redirects to
# `Category.objects.get_tree()` — which Oscar's `CategoryQuerySet.as_manager()`
# never exposes, causing AttributeError on every category page. 4.5.1 keeps
# `get_tree` on the model, matching Oscar 4.1's expectation.
RUN pip install --no-cache-dir "django-treebeard==4.5.1"

# PayPal Express Checkout facade uses plain `requests` against PayPal's REST API
RUN pip install --no-cache-dir requests

# Build frontend assets (gulp copy + scss). Non-fatal so the app still starts
# even if SCSS compilation fails in this environment.
RUN npm install && npm run build || echo "npm build skipped: frontend assets may be missing"

# Oscar only ships its precompiled static assets (styles.css, dashboard.css, JS,
# webfonts) inside the PyPI wheel — the Git source tree gitignores them as build
# artifacts. Without copying them into the editable install, every page 404s on
# /static/oscar/css/styles.css and the whole UI loses styling. Pull the wheel
# matching the installed Oscar version and extract its static into the package.
RUN PIP_VER="$(python -c 'import importlib.metadata as m; print(m.version("django-oscar"))')" \
 && pip download --no-deps -d /tmp/oscar_whl "django-oscar==$PIP_VER" \
 && python - <<'PY'
import zipfile, glob, os, shutil
whl = glob.glob('/tmp/oscar_whl/*.whl')[0]
with zipfile.ZipFile(whl) as z:
    z.extractall('/tmp/oscar_static')
src = '/tmp/oscar_static/oscar/static/oscar'
dst = '/app/src/oscar/static/oscar'
os.makedirs(os.path.dirname(dst), exist_ok=True)
if os.path.isdir(dst):
    shutil.rmtree(dst)
shutil.copytree(src, dst)
shutil.rmtree('/tmp/oscar_whl')
shutil.rmtree('/tmp/oscar_static')
PY

USER django

WORKDIR /app/sandbox/

# Install uwsgi
USER root
RUN pip install --no-cache-dir uwsgi
USER django

CMD ["/bin/bash", "/app/init-db.sh"]
