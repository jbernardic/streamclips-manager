import errno
import os
import signal
import subprocess
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
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

def start_process(db: Session, streamer_id: str):
    # Start new process
    proc = subprocess.Popen([
        "python", "/home/janbernardic/socialagents/streamclips_mock.py", 
        str(streamer_id)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Save to database
    new_process = models.StreamClipsProcess(
        streamer_id=streamer_id,
        pid=proc.pid
    )
    db.add(new_process)
    db.commit()
    db.refresh(new_process)
    return new_process

def is_alive(process_id: str):
    if process_id <= 0:
        return False
    try:
        # signal 0 doesn't kill the process but checks if it's running
        os.kill(process_id, 0)
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
        raise HTTPException(status_code=404, detail="Process not found")
    
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
    finally:
        db.close()