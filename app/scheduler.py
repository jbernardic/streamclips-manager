from datetime import datetime, timezone
import os
import signal
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from app.core import stream_clips_processes, instances
from app.database.connection import get_db
from app.database import models


scheduler = BackgroundScheduler()


def process_active_streamers():
    """Start processes for active streamers on this instance"""
    db = next(get_db())
    try:
        hostname = instances.get_current_hostname()
        
        # Register/update instance and heartbeat
        instances.update_heartbeat(db, hostname)
        
        # Clean up dead instances
        dead_instances = instances.get_dead_instances(db)
        for dead_instance in dead_instances:
            cleaned_count = instances.cleanup_dead_instance_processes(db, dead_instance.hostname)
            if cleaned_count > 0:
                print(f"Cleaned up {cleaned_count} processes from dead instance {dead_instance.hostname}")
        
        # Check capacity for this instance
        available_capacity = instances.get_available_capacity(db, hostname)
        if available_capacity <= 0:
            print(f"Instance {hostname} at capacity")
            return
        
        # Claim available streamers with locking
        claimed_streamers = instances.claim_available_streamers(db, hostname, available_capacity)
        
        # Start processes for claimed streamers
        for streamer in claimed_streamers:
            try:
                proc = stream_clips_processes.start_process(db=db, streamer=streamer, instance_hostname=hostname)
                print(f"Started process for {streamer.name} on {hostname} (PID: {proc.pid})")
            except Exception as e:
                print(f"Failed to start process for {streamer.name}: {e}")
                db.rollback()
        
        # Health check existing processes for this instance
        my_processes = instances.get_instance_processes(db, hostname)
        for process in my_processes:
            now = datetime.now(tz=timezone.utc)
            elapsed = (now - process.updated_at).total_seconds()
            if elapsed > 45:
                try:
                    stream_clips_processes.stop_process(db, str(process.id))
                    print(f"Stopped inactive process. PID {process.pid}, Streamer {process.streamer.name}")
                except Exception as e:
                    print(f"Error stopping process {process.id}: {e}")
                
    except Exception as e:
        print(f"Error in scheduler: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start the scheduler"""
    scheduler.add_job(
        process_active_streamers,
        trigger='interval',
        minutes=1,
        id='process_active_streamers',
        next_run_time=datetime.now()
    )
    scheduler.start()
    print("Scheduler started")


def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    print("Scheduler stopped")