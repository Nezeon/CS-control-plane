"""
Ensure the admin user exists on startup (no seed data).

Creates ayushmaan@hivepro.com if it doesn't exist.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SyncSessionLocal
from app.models.user import User
from app.utils.security import hash_password

logger = logging.getLogger("startup")

ADMIN_EMAIL = "ayushmaan@hivepro.com"
ADMIN_NAME = "Ayushmaan Singh Naruka"
ADMIN_PASSWORD = "password123"


def ensure_admin_user():
    """Create the admin user if it doesn't exist. No other data is created."""
    db = SyncSessionLocal()
    try:
        existing = db.execute(
            select(User).where(User.email == ADMIN_EMAIL)
        ).scalar_one_or_none()

        if existing:
            logger.info(f"Admin user {ADMIN_EMAIL} already exists.")
            return

        user = User(
            id=uuid.uuid4(),
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            full_name=ADMIN_NAME,
            role="admin",
        )
        db.add(user)
        db.commit()
        logger.info(f"Created admin user: {ADMIN_EMAIL}")
    finally:
        db.close()
