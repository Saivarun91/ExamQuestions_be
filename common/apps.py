from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self):
        # Avoid double-warm under Django runserver autoreloader parent process.
        import os
        import sys

        is_runserver = any(
            arg == "runserver" or arg.endswith("runserver") for arg in sys.argv
        )
        if is_runserver and os.environ.get("RUN_MAIN") != "true":
            return

        try:
            from backend.sitemap import warm_sitemaps_on_startup

            warm_sitemaps_on_startup()
        except Exception:
            # Sitemap warm is best-effort; never block app boot.
            pass
