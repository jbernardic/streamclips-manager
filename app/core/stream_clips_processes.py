import errno
import os
import signal
import subprocess
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import models


def get(db: Session, id: str) -> Optional[models.StreamClipsProcess]:
    """Get a process by ID"""
    return db.query(models.StreamClipsProcess).filter(
        models.StreamClipsProcess.id == id
    ).first()


def list_all(db: Session) -> List[models.StreamClipsProcess]:
    """List all processes"""
    return db.query(models.StreamClipsProcess).all()

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

def stop_process(db: Session, process_id: str):
    """Stop a process and delete the record"""
    process = get(db, process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    # Kill the process
    try:
        os.kill(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass  # Process already dead
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop process: {e}")
    
    # Delete from database
    db.delete(process)
    db.commit()


def delete(db: Session, process_id: str):
    """Delete a process record"""
    process = get(db, process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    db.delete(process)
    db.commit()