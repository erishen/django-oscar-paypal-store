from oscar.apps.dashboard.orders.apps import (
    OrdersDashboardConfig as CoreOrdersDashboardConfig,
)


class OrdersDashboardConfig(CoreOrdersDashboardConfig):
    name = 'apps.dashboard.orders'
