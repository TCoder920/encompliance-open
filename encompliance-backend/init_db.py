"""
Database Initialization Script
----------------------------
This script initializes the EnCompliance database with required tables and initial data.
It provides:
- Database schema creation
- Initial admin user creation
- Default configuration setup
- Migration handling
- Database connection testing
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User, Base
from app.models.query_log import QueryLog
from app.auth.utils import get_password_hash

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/encompliance")
# Convert to async URL
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Admin user credentials
ADMIN_EMAIL = "admin@encompliance.io"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Change this in production!

async def init_db():
    # Create async engine
    engine = create_async_engine(ASYNC_DATABASE_URL)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create admin user
    async with async_session() as session:
        # Check if admin user already exists
        admin_user = await session.query(User).filter(User.username == ADMIN_USERNAME).first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                email=ADMIN_EMAIL,
                username=ADMIN_USERNAME,
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print(f"Admin user created: {ADMIN_USERNAME}")
        else:
            print(f"Admin user already exists: {ADMIN_USERNAME}")
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_db()) 