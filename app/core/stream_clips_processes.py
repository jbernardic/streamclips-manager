import errno
import os
import signal
import subprocess
import threading
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core import logs
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

def start_process(db: Session, streamer: models.Streamer):
    # Start new process
    proc = subprocess.Popen([
        "python", "-u", "streamclips",
        streamer.url,
        "--output-dir", "clips",
        "--clip-duration", "60.0",
        "--window-timespan", "30.0",
        "--sample-interval", "1",
        "--baseline-duration", "180",
        "--surge-threshold", "2.0"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, 
    start_new_session=True)
    
    # Save to database
    new_process = models.StreamClipsProcess(
        streamer_id=streamer.id,
        pid=proc.pid
    )
    db.add(new_process)
    db.commit()
    db.refresh(new_process)
    monitor_process_output(proc, new_process, streamer)
    return new_process

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

def is_alive(pid: int):
    if pid <= 0:
        return False
    try:
        # signal 0 doesn't kill the process but checks if it's running
        os.kill(pid, 0)
    except OSError as e:
        if e.errno == errno.ESRCH:
            # No such process
            return False
        elif e.errno == errno.EPERM:
            # Process exists but no permission to signal it
            return True
        else:
            # Other errors
            raise
    else:
        # No exception means process exists
        return True

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
            except ProcessLookupError:
                # Process already dead
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