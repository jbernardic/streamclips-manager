import os
from markupsafe import Markup
from sqladmin import Admin, ModelView
from .database import models, connection
from .admin_auth import AdminAuth


class StreamerAdmin(ModelView, model=models.Streamer):
    column_list = [models.Streamer.name, models.Streamer.url, models.Streamer.is_active, models.Streamer.stream_clips_process]

    column_formatters = {
        models.Streamer.url: lambda m, a: Markup(f"<a target=\"_blank\" href={getattr(m, a)}>{getattr(m, a)}</a>")
    }
    
class LogAdmin(ModelView, model=models.Log):
    column_list = [models.Log.created_at, models.Log.source, models.Log.level, models.Log.message]
    column_default_sort = (models.Log.created_at, True)

class StreamConfigAdmin(ModelView, model=models.StreamConfig):
    column_list = [models.StreamConfig.clip_duration, models.StreamConfig.window_timespan, 
                   models.StreamConfig.sample_interval, models.StreamConfig.baseline_duration, 
                   models.StreamConfig.surge_threshold, models.StreamConfig.updated_at]
    column_default_sort = (models.StreamConfig.updated_at, True)
    
    # Only allow editing the first (and only) record
    can_create = False
    can_delete = False
    
    def get_list_query(self):
        """Ensure only one record exists and return it."""
        from .database.connection import get_db
        db = next(get_db())
        try:
            # Get or create the singleton config
            from .core.stream_clips_processes import get_stream_config
            get_stream_config(db)
            return super().get_list_query().limit(1)
        finally:
            db.close()

def init(app):
    authentication_backend = AdminAuth(secret_key=os.getenv("SECRET_KEY"))
    app.admin = Admin(app, connection.engine, authentication_backend=authentication_backend)

    app.admin.add_view(StreamerAdmin)
    app.admin.add_view(LogAdmin)
    app.admin.add_view(StreamConfigAdmin)

    