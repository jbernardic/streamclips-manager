import os
from app.core import auth
from app.database import connection, models

def create_admin_user():
    db = connection.SessionLocal()
    admin = db.query(models.User).filter(models.User.is_admin == True).first()
    if not admin:
        admin_user = models.User(
            username="admin",
            password_hash=auth.hash_password(os.getenv("ADMIN_PASSWORD", "defaultpassword")),
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()
    db.close()