import os
from fastapi.responses import RedirectResponse
from markupsafe import Markup
from sqladmin import Admin, ModelView, BaseView, expose, action
from .database import models, connection
from .admin_auth import AdminAuth

from .database.connection import get_db

class StreamerAdmin(ModelView, model=models.Streamer):
    column_list = [models.Streamer.name, models.Streamer.url, models.Streamer.is_active, models.Streamer.stream_clips_process]

    column_formatters = {
        models.Streamer.url: lambda m, a: Markup(f"<a target=\"_blank\" href={getattr(m, a)}>{getattr(m, a)}</a>")
    }
    
class LogAdmin(ModelView, model=models.Log):
    column_list = [models.Log.created_at, models.Log.source, models.Log.level, models.Log.message]
    column_default_sort = (models.Log.created_at, True)
    
    @action(
        name="delete_all",
        label="Delete all items",
        add_in_list=True
    )
    async def delete_all_logs(self, request):
        db = next(get_db())
        try:
            db.query(models.Log).delete()
            db.commit()
            return RedirectResponse(url=request.url_for("admin:list", identity="log"), status_code=302)
        finally:
            db.close()

class StreamConfigAdmin(ModelView, model=models.StreamConfig):
    name_plural = "Stream Config"
    
    column_list = [models.StreamConfig.clip_duration, models.StreamConfig.window_timespan, 
                   models.StreamConfig.sample_interval, models.StreamConfig.baseline_duration, 
                   models.StreamConfig.surge_threshold, models.StreamConfig.updated_at]
    column_default_sort = (models.StreamConfig.updated_at, True)
    
    # Only allow editing the first (and only) record
    can_create = False
    can_delete = False

class FileBrowserView(BaseView):
    name = "File Browser"
    icon = "fa-solid fa-folder"
    
    def is_accessible(self, request):
        return os.getenv("STORAGE_SERVER_HOST") != None
        
    @expose("/file-browser", methods=["GET"])
    async def redirect(self, request):
        return RedirectResponse(url=f"https://{os.getenv('STORAGE_SERVER_HOST')}")

def init(app):
    authentication_backend = AdminAuth(secret_key=os.getenv("SECRET_KEY"))
    app.admin = Admin(app, connection.engine, authentication_backend=authentication_backend)

    app.admin.add_view(StreamerAdmin)
    app.admin.add_view(StreamConfigAdmin)
    app.admin.add_view(LogAdmin)
    app.admin.add_view(FileBrowserView)
    