#!/bin/bash
echo "=========================================="
echo "Initializing Django Oscar Database"
echo "=========================================="

cd /app/sandbox

# Skip database waiting, Docker handles it with healthcheck
echo "Initializing database..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput || echo "Migration failed, continuing anyway..."

# Check if data exists
USER_COUNT=$(python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())" 2>/dev/null || echo "0")
if [ "$USER_COUNT" -lt 1 ]; then
    echo "Loading initial data..."
    python manage.py loaddata fixtures/auth.json
    python manage.py loaddata fixtures/child_products.json
    python manage.py oscar_import_catalogue fixtures/*.csv
    python manage.py oscar_import_catalogue_images fixtures/images.tar.gz
    python manage.py oscar_populate_countries --initial-only
    python manage.py loaddata fixtures/pages.json fixtures/ranges.json fixtures/offers.json
    python manage.py loaddata fixtures/orders.json
    python manage.py collectstatic --noinput
    echo "Initial data loaded successfully!"
else
    echo "Data already exists. Skipping data loading."
fi

# Always rebuild search index to ensure it's available
echo "Rebuilding search index..."
python manage.py clear_index --noinput
python manage.py update_index catalogue
python manage.py thumbnail cleanup

echo "=========================================="
echo "Initialization complete!"
echo "=========================================="

# Copy missing image
cp --remove-destination /app/src/oscar/static/oscar/img/image_not_found.jpg /app/sandbox/public/media/ 2>/dev/null || true

# Start uWSGI
echo "Starting uWSGI..."
exec uwsgi --ini /app/sandbox/uwsgi.ini



