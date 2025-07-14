import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from app.core import stream_clips_processes
from app.database.connection import get_db
from app.database import models


scheduler = BackgroundScheduler()


def process_active_streamers():
    """Start processes for active streamers"""
    db = next(get_db())
    try:
        # Get active streamers
        active_streamers = db.query(models.Streamer).filter(
            models.Streamer.is_active == True
        ).all()
        
        for streamer in active_streamers:
            # Check if already has running process
            existing = db.query(models.StreamClipsProcess).filter(
                models.StreamClipsProcess.streamer_id == streamer.id
            ).first()
            
            if not existing:
                proc = stream_clips_processes.start_process(db=db, streamer_id=streamer.id)
                print(f"Started process for {streamer.name} (PID: {proc.pid})")
            else:
                if not stream_clips_processes.is_alive(existing.pid):
                    stream_clips_processes.delete(db, existing.id)
                
    except Exception as e:
        print(f"Error in scheduler: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the scheduler"""
    scheduler.add_job(
        process_active_streamers,
        trigger='interval',
        minutes=1,
        id='process_active_streamers'
    )
    scheduler.start()
    print("Scheduler started")


def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    print("Scheduler stopped")