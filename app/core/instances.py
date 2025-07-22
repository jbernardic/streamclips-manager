import os
import socket
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import exists
from app.database import models
from app.database.connection import get_db


def get_current_hostname() -> str:
    """Get the current instance hostname"""
    return os.getenv("INSTANCE_ID", socket.gethostname())


def register_instance() -> models.Instance:
    """Register or update instance in database"""
    hostname = get_current_hostname()
    max_processes = os.getenv("INSTANCE_MAX_PROCESSES", 5)

    db = next(get_db())
    try:    
        instance = db.query(models.Instance).filter(
            models.Instance.hostname == hostname
        ).first()

        if instance:
            instance.max_processes=max_processes,
            instance.last_heartbeat = datetime.now(tz=timezone.utc)
        else:
            # Create new instance
            instance = models.Instance(
                max_processes=max_processes,
                hostname=hostname,
                created_at=datetime.now(tz=timezone.utc),
                last_heartbeat=datetime.now(tz=timezone.utc)
            )
            db.add(instance)

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return instance


def update_heartbeat(db: Session, hostname: str = None):
    """Update instance heartbeat"""
    if hostname is None:
        hostname = get_current_hostname()
    
    instance = db.query(models.Instance).filter(
        models.Instance.hostname == hostname
    ).first()
    
    if instance:
        instance.last_heartbeat = datetime.now(tz=timezone.utc)
        db.commit()


def get_instance_load(db: Session, hostname: str = None) -> int:
    """Get current process count for instance"""
    if hostname is None:
        hostname = get_current_hostname()
    
    return db.query(models.StreamClipsProcess).filter(
        models.StreamClipsProcess.instance_hostname == hostname
    ).count()


def get_available_capacity(db: Session, hostname: str = None) -> int:
    """Get available capacity for instance"""
    if hostname is None:
        hostname = get_current_hostname()
    
    instance = db.query(models.Instance).filter(
        models.Instance.hostname == hostname
    ).first()
    
    if not instance:
        return 0
    
    current_load = get_instance_load(db, hostname)
    return max(0, instance.max_processes - current_load)


def claim_available_streamers(db: Session, hostname: str = None, max_count: int = None) -> List[models.Streamer]:
    """Claim available streamers with database locking"""
    if hostname is None:
        hostname = get_current_hostname()
    
    if max_count is None:
        max_count = get_available_capacity(db, hostname)
    
    if max_count <= 0:
        return []
    
    # 1 minute cooldown period
    cooldown_cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    
    # Find streamers without processes and not recently processed
    available_streamers = db.query(models.Streamer).filter(
        models.Streamer.is_active == True,
        ~exists().where(models.StreamClipsProcess.streamer_id == models.Streamer.id),
        # Exclude streamers processed within cooldown period
        (models.Streamer.last_processed_at.is_(None)) | 
        (models.Streamer.last_processed_at < cooldown_cutoff)
    ).with_for_update(skip_locked=True).limit(max_count).all()
    
    return available_streamers


def get_instance_processes(db: Session, hostname: str = None) -> List[models.StreamClipsProcess]:
    """Get all processes for specific instance"""
    if hostname is None:
        hostname = get_current_hostname()
    
    return db.query(models.StreamClipsProcess).filter(
        models.StreamClipsProcess.instance_hostname == hostname
    ).all()


def get_dead_instances(db: Session, timeout_minutes: int = 5) -> List[models.Instance]:
    """Get instances that haven't sent heartbeat recently"""
    cutoff_time = datetime.now(tz=timezone.utc) - timedelta(minutes=timeout_minutes)
    
    return db.query(models.Instance).filter(
        models.Instance.last_heartbeat < cutoff_time
    ).all()


def cleanup_dead_instance_processes(db: Session, hostname: str):
    """Clean up processes from dead instance"""
    processes = db.query(models.StreamClipsProcess).filter(
        models.StreamClipsProcess.instance_hostname == hostname
    ).all()
    
    for process in processes:
        # Update streamer's last_processed_at timestamp
        if process.streamer:
            process.streamer.last_processed_at = datetime.now(timezone.utc)
        db.delete(process)
    
    db.commit()
    return len(processes)


def get_all_instances(db: Session) -> List[models.Instance]:
    """Get all registered instances"""
    return db.query(models.Instance).all()