from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models, auth
from sqlalchemy.exc import IntegrityError
import uuid

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
ADMIN_ROLE = "admin"


def seed_admin() -> None:
    db: Session = SessionLocal()
    try:
        # ensure tables exist
        models.Base.metadata.create_all(bind=engine)
        # check if admin exists by username or email
        user = (
            db.query(models.User)
            .filter(
                (models.User.username == ADMIN_USERNAME)
                | (models.User.email == ADMIN_EMAIL)
            )
            .first()
        )
        if user:
            print(f"Admin already exists: {user.username} ({user.email})")
            return
        # create admin
        password_hash = auth.get_password_hash(ADMIN_PASSWORD)
        admin = models.User(
            id=uuid.uuid4(),
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=password_hash,
            role=ADMIN_ROLE,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("Seeded default admin user:")
        print(f"  username: {ADMIN_USERNAME}")
        print(f"  email:    {ADMIN_EMAIL}")
        print(f"  password: {ADMIN_PASSWORD}")
    except IntegrityError:
        db.rollback()
        print("Admin user already present (integrity).")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
