import os
from app.core import auth
from app.database import models
from app.database.connection import get_db

def create_admin_user():
    db = next(get_db())
    try:
        admin = db.query(models.User).filter(models.User.is_admin == True).first()
        if not admin:
            admin_user = models.User(
                username="admin",
                password_hash=auth.hash_password(os.getenv("ADMIN_PASSWORD", "defaultpassword")),
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()