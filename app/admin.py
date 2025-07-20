import os
from fastapi import Request
from fastapi.responses import RedirectResponse
from markupsafe import Markup
from sqladmin import Admin, ModelView, BaseView, expose, action
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core import instances
from .database import models, connection
from .admin_auth import AdminAuth
from .database.connection import get_db

class StreamerAdmin(ModelView, model=models.Streamer):
    column_list = [models.Streamer.name, models.Streamer.url, models.Streamer.is_active, "processed_by"]
    form_excluded_columns = [models.Streamer.stream_clips_process]

    def list_query(self, request: Request):
        return select(models.Streamer).options(
            selectinload(models.Streamer.stream_clips_process)
        )
    
    def processed_by(self, obj):
        """Show which instance is processing this streamer"""
        # Now this should work because relationship is eagerly loaded
        if hasattr(obj, 'stream_clips_process') and obj.stream_clips_process:
            return obj.stream_clips_process.instance_hostname
        return "Not running"
    
    column_formatters = {
        models.Streamer.url: lambda m, a: Markup(f"<a target=\"_blank\" href=\"{getattr(m, a)}\">{getattr(m, a)}</a>"),
        "processed_by": lambda m, a: StreamerAdmin.processed_by(None, m)
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
    column_list = [
        models.StreamConfig.clip_duration,
        models.StreamConfig.window_timespan,
        models.StreamConfig.sample_interval,
        models.StreamConfig.baseline_duration,
        models.StreamConfig.surge_threshold,
        models.StreamConfig.updated_at
    ]
    column_default_sort = (models.StreamConfig.updated_at, True)
    
    # Only allow editing the first (and only) record
    can_create = False
    can_delete = False

class InstanceAdmin(ModelView, model=models.Instance):
    column_list = [
        models.Instance.hostname,
        models.Instance.max_processes,
        "current_load",
        models.Instance.created_at,
        models.Instance.last_heartbeat
    ]
    column_default_sort = (models.Instance.last_heartbeat, True)
    
    def list_query(self, request: Request):
        return select(models.Instance).options(
            selectinload(models.Instance.processes)
        )
    
    def current_load(self, obj):
        """Show current load in format 'current/max'"""
        # Now this should work because processes relationship is eagerly loaded
        current = len(obj.processes) if hasattr(obj, 'processes') and obj.processes else 0
        return f"{current}/{obj.max_processes}"
    
    # Read-only - instances are managed automatically
    can_create = False
    can_delete = False
    can_edit = False
    
    column_formatters = {
        "current_load": lambda m, a: InstanceAdmin.current_load(None, m)
    }

class FileBrowserView(BaseView):
    name = "File Browser"
    icon = "fa-solid fa-folder"
    
    def is_accessible(self, request):
        return os.getenv("STORAGE_SERVER_HOST") is not None
    
    @expose("/file-browser", methods=["GET"])
    async def redirect(self, request):
        return RedirectResponse(url=f"https://{os.getenv('STORAGE_SERVER_HOST')}")

def init(app):
    authentication_backend = AdminAuth(secret_key=os.getenv("SECRET_KEY"))
    app.admin = Admin(app, connection.engine, authentication_backend=authentication_backend)
    app.admin.add_view(InstanceAdmin)
    app.admin.add_view(StreamerAdmin)
    app.admin.add_view(StreamConfigAdmin)
    app.admin.add_view(LogAdmin)
    app.admin.add_view(FileBrowserView)