import os
from sqladmin import Admin, ModelView
from .database import models, connection
from .admin_auth import AdminAuth


class StreamerAdmin(ModelView, model=models.Streamer):
    column_list = [models.Streamer.name, models.Streamer.url, models.Streamer.is_active, models.Streamer.process_count]
    
class LogAdmin(ModelView, model=models.Log):
    column_list = [models.Log.created_at, models.Log.source, models.Log.level, models.Log.message]
    column_default_sort = (models.Log.created_at, True)

def init(app):
    authentication_backend = AdminAuth(secret_key=os.getenv("SECRET_KEY"))
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    app.admin = Admin(app, connection.engine, templates_dir=templates_dir, authentication_backend=authentication_backend)

    app.admin.add_view(StreamerAdmin)
    app.admin.add_view(LogAdmin)

    