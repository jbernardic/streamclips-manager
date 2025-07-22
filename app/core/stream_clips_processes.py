import asyncio
from datetime import datetime, timezone
import psutil
import os
import signal
import subprocess
import threading
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core import configs, logs
from app.database import models
from app.database.connection import get_db


def get(db: Session, id: str) -> Optional[models.StreamClipsProcess]:
    """Get a process by ID"""
    return db.query(models.StreamClipsProcess).filter(
        models.StreamClipsProcess.id == id
    ).first()


def list_all(db: Session) -> List[models.StreamClipsProcess]:
    """List all processes"""
    return db.query(models.StreamClipsProcess).all()

def delete(db: Session, process_id: str):
    """Delete a process record"""
    process = get(db, process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    db.delete(process)
    db.commit()

def start_process(db: Session, streamer: models.Streamer, instance_hostname: str):
    # Get configuration
    config = configs.get_stream_config(db)
    
    # Build command with configuration
    cmd = [
        "python", "-u", "streamclips",
        streamer.url,
        "--output-dir", f"clips/{streamer.name}",
        "--clip-duration", str(config.clip_duration),
        "--window-timespan", str(config.window_timespan),
        "--sample-interval", str(config.sample_interval),
        "--baseline-duration", str(config.baseline_duration),
        "--surge-threshold", str(config.surge_threshold)
    ]
    
    # Add storage server if env vars are set
    storage_user = os.environ.get("STORAGE_SERVER_USER")
    storage_host = os.environ.get("STORAGE_SERVER_HOST")
    storage_password = os.environ.get("STORAGE_SERVER_PASSWORD")
    storage_path = os.environ.get("STORAGE_SERVER_PATH")
    if storage_user and storage_host:
        cmd.extend(["--storage-server", f"{storage_user}@{storage_host}"])
        if storage_password:
            cmd.extend(["--storage-password", storage_password])
        if storage_path:
            cmd.extend(["--storage-path", storage_path])
    
    # Start new process
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, 
    start_new_session=True)
    
    # Save to database
    new_process = models.StreamClipsProcess(
        streamer_id=streamer.id,
        instance_hostname=instance_hostname,
        pid=proc.pid
    )
    db.add(new_process)
    db.commit()
    db.refresh(new_process)
    monitor_process_output(proc, new_process, streamer)
    return new_process

async def is_hanging(pid):
    check_duration = 10
    cpu_threshold = 0.00

    try:
        p = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return False  # Process does not exist
    
    cpu_start = p.cpu_times()
    await asyncio.sleep(check_duration)
    cpu_end = p.cpu_times()
    
    cpu_diff = (cpu_end.user - cpu_start.user) + (cpu_end.system - cpu_start.system)
    return cpu_diff/check_duration <= cpu_threshold

async def stop_if_inactive(db_proc_id: int, pid: int):
    hanging = await is_hanging(pid)
    if hanging:
        db = next(get_db())
        try:
            stop_process(db, db_proc_id)
        except Exception:
            db.rollback()
        finally:
            db.close()

def monitor_process_output(proc: subprocess.Popen, process: models.StreamClipsProcess, streamer: models.Streamer):
    source_name = streamer.name
    db_proc_id = process.id
    for stream_name, stream in [("stdout", proc.stdout), ("stderr", proc.stderr)]:
        if stream is None:
            continue
        def reader(s, name, db_proc_id, source_name):
            db = next(get_db())
            try:
                for line in iter(s.readline, ''):
                    if not line: #EOF
                        break
                    if line.strip():
                        level = models.LogLevel.INFO if name == "stdout" else models.LogLevel.ERROR
                        logs.create(db, source=f"streamclips-{source_name}", message=line.strip(), level=level)
                # cleanup
                stop_process(db, db_proc_id)
            except Exception as e:
                print(f"Error logging output: {e}")
                db.rollback()
            finally:
                db.close()
        threading.Thread(target=reader, args=(stream,stream_name, db_proc_id, source_name), daemon=True).start()

def kill_process(pid: int):
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Killed process PID {pid}")
    except ProcessLookupError:
        pass  # Process already dead
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to kill process: {e}")

def stop_process(db: Session, id: str):
    """Stop a process and delete the record"""
    process = get(db, id)
    if not process:
        return
    
    # Kill the process
    kill_process(process.pid)
    
    # Update streamer's last_processed_at timestamp
    if process.streamer:
        process.streamer.last_processed_at = datetime.now(timezone.utc)
    
    # Delete from database
    db.delete(process)
    db.commit()


def stop_all_processes():
    """Stop all running processes"""
    db = next(get_db())
    try:
        # Get all processes from database
        all_processes = list_all(db)
        
        for process in all_processes:
            try:
                # Kill the process
                os.kill(process.pid, signal.SIGTERM)
                print(f"Stopped process PID {process.pid}")
                
                # Update streamer's last_processed_at timestamp
                if process.streamer:
                    process.streamer.last_processed_at = datetime.now(timezone.utc)
                    
            except ProcessLookupError:
                # Process already dead, still update timestamp
                if process.streamer:
                    process.streamer.last_processed_at = datetime.now(timezone.utc)
                pass
            except Exception as e:
                print(f"Error stopping process {process.pid}: {e}")
        
        # Clear all process records from database
        db.query(models.StreamClipsProcess).delete()
        db.commit()
        print("All processes stopped and cleaned up")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

def stop_instance_processes(instance_hostname: str):
    """Stop all processes for specific instance"""
    db = next(get_db())
    try:
        processes = db.query(models.StreamClipsProcess).filter(
            models.StreamClipsProcess.instance_hostname == instance_hostname
        ).all()
        
        for process in processes:
            try:
                kill_process(process.pid)
                
                # Update streamer's last_processed_at timestamp
                if process.streamer:
                    process.streamer.last_processed_at = datetime.now(timezone.utc)
                
                db.delete(process)
                print(f"Stopped process PID {process.pid} from instance {instance_hostname}")
            except Exception as e:
                print(f"Error stopping process {process.pid}: {e}")
        
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()