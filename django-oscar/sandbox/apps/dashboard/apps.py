from oscar.apps.dashboard.apps import DashboardConfig as CoreDashboardConfig


class DashboardConfig(CoreDashboardConfig):
    # Forking the *top-level* dashboard app is required for Oscar's
    # dynamic class loader to pick up forked dashboard sub-apps:
    # get_class('dashboard.orders.views', ...) resolves the app from the
    # FIRST label segment ('dashboard'), then joins this app's name with
    # the remaining path -> 'apps.dashboard.orders.views'.
    name = 'apps.dashboard'
